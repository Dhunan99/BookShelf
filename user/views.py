from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import login as lg, authenticate
from django.contrib.auth.models import User
from .forms import NewUserForm,UserBioChangeForm,CustomUserChangeForm,UserBioChangeForm2,EmailChange,NumberChange,UserProfileChangeForm
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView,PasswordResetDoneView,PasswordResetCompleteView,PasswordResetConfirmView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import User
from .models import OTPModel,ShoppingCart,PurchaseHistory,Notification,UserActivity,UserProfile,NotificationType
from pyotp import TOTP
from django.http import JsonResponse
import secrets
from django.core.mail import send_mail
from django.contrib.auth.views import PasswordChangeView
from books.models import Books,Review
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.template.loader import get_template
from django.template import Context
import datetime
from xhtml2pdf import pisa
from io import BytesIO
from decimal import Decimal
from django.views.decorators.cache import cache_control
from django.db.models import Sum
from .models import Message
from django.db import models
import json
from django.db.models import Q
from datetime import timedelta
from django.core.cache import cache

  # Import User model
# from django.contrib import messages
# from django.contrib.auth import authenticate, login
# from django.contrib.auth.forms import AuthenticationForm
# from .forms import RegisterForm
# from django.core.mail import send_mail
# from django.core.mail import EmailMultiAlternatives
# from django.template.loader import get_template
# from django.template import Context
# Create your views here.

class CustomPasswordResetView(PasswordResetView):
    template_name = 'user/password_reset_form.html'  # Your template for the password reset form
    email_template_name = 'user/password_reset_email.html'  # Your email template for the password reset email
    success_url = reverse_lazy('password_reset_done')  # URL to redirect after successful form submission
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'user/password_reset_done.html'  # Your template for password reset done page
    
def login(request):
    error_message=""
    if request.user.is_authenticated:
        logout(request)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            lg(request, user)
            # if user.is_superuser:
            #     return redirect('/admin')
            return redirect('/user/home',{'user',user})
        else:
            error_message = "Invalid login credentials"
    return render(request, 'user/login.html',{'error':error_message})

@login_required  # Add this decorator to ensure the user is authenticated
def mark_notifications_as_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'message': 'Notifications marked as read successfully'})
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=400)

@login_required
def notifications_view(request):
    user = request.user
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-timestamp')
    # Mark notifications as read when the user views them
    # for notification in unread_notifications:
    #     notification.mark_as_read()

    # Create a list of notification messages
    if unread_notifications:
        notification_messages = [notification.notification_message for notification in unread_notifications]
    else:
        notification_messages = ["No notifications at the moment"]
    # Render the notification messages to HTML
    notification_html = render_to_string('notifications.html', {'notification_messages': notification_messages})
    unread_count = unread_notifications.count()

    # Return the notification messages as a JSON response
    return JsonResponse({'notification_messages': notification_html,'unread_count': unread_count})

def register(request):
        if request.user.is_authenticated:
            logout(request)
        context=None
        if request.method == "POST":
                form = NewUserForm(request.POST)
                if form.is_valid():
                    user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password1'])
                    otp = TOTP('JBSWY3DPEHPK3PXP').now()  # Replace with your secret key
                    user.is_active = False
                    user.save()
                    otp_record = OTPModel.objects.create(user=user, otp=otp, expires_at=timezone.now() + timezone.timedelta(minutes=10))
                    # Send OTP to user's email
                    send_otp_email(user.email, otp)
                    # Redirect user to OTP verification page
                    return redirect('verify_otp', user_id=user.id)
                    # user = authenticate(username=user.username, password=form.cleaned_data['password1'])
                    # lg(request, user)
                    # context= {'form': form}
                    # messages.success(request, "Registration successful." )
                else:
                     context={'form':form}
        return render (request,"user/register.html",context)

def verify_otp(request, user_id=None):
    user = User.objects.get(id=user_id)
    otp_record = OTPModel.objects.filter(user=user, expires_at__gt=timezone.now()).first()

    if not otp_record:
        return redirect('registration')  # Redirect if OTP is expired or not found

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')

        if entered_otp == otp_record.otp:
            otp_record.delete()  # Delete OTP record after successful verification
            user.is_active = True
            user.save()
            return redirect('login')  # Redirect to login page

    return render(request, 'user/verify_otp.html')

def send_otp_email(to_email, otp):
    subject = 'Your OTP for Registration'
    message = f'Thank you for registering with our website!\n\n'
    message += f'Your One-Time Password (OTP) for email verification is: {otp}\n\n'
    message += 'Please enter this OTP on our website to complete your registration.\n\n'
    message += 'If you did not sign up for an account, you can ignore this email.\n\n'
    message += 'Thank you for choosing our service!\n\n'
    message += 'Best regards,\nBookShelf'
    from_email = 'midhunkrishnanm2024@mca.ajce.in'  # Replace with your email
    send_mail(subject, message, from_email, [to_email])

class ChangePasswordView(PasswordChangeView):
    template_name = 'user/change_password.html'  # Create a template for the change password page
    success_url = reverse_lazy('user_profile')  # Redirect to the profile page after successfully changing the password

def validate_username(request):
    username = request.GET.get('username', None)
    data = {    
        'is_taken': User.objects.filter(username__iexact=username).exists()
    }
    return JsonResponse(data)
# def register(request):
#     if request.method == 'POST':
#         form = RegistrationForm(request.POST)
#         print(form)
#         if form.is_valid():
#             print("asdas")
#             form.save()
#             return redirect('home')
#     else:
#         form = RegistrationForm()
#     return render(request, 'user/register.html', {'form': form})
    # if request.method == 'POST':
  
    #     # AuthenticationForm_can_also_be_used__
  
    #     username = request.POST['username']
    #     password = request.POST['password']
    #     user = authenticate(request, username = username, password = password)
    #     if user is not None:
    #         form = login(request, user)
    #         messages.success(request, f' welcome {username} !!')
    #         return redirect('index')
    #     else:
    #         messages.info(request, f'account done not exit plz sign in')
    # form = AuthenticationForm()
    # return render(request, 'user/login.html', {'form':form, 'title':'log in'})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def home(request):
    if not cache.get('last_comprehensive_score_update'):
        Books.assign_tags()
        cache.set('last_comprehensive_score_update', True, 1)
    for book in Books.objects.all():
            # Loop through all reviews for the current book
            for review in Review.objects.filter(book=book):
                # Combine the review text with overall rating for sentiment analysis
                review.calculate_sentiment_score()
    # Fetch book data from the Books model
    books = Books.objects.filter(tags__name='Popular')
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    context = {
        'books': books,
        'cart_item_count':cart_item_count,

    }
    
    return render(request,'user/home.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def user_profile(request):
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    return render(request,'user/profile.html',{'cart_item_count':cart_item_count})


@login_required
def save_profile(request):
    if request.method == 'POST':
        form_name = request.POST.get('form_name') 
        if form_name == 'user':
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
            form = UserProfileChangeForm(request.POST, request.FILES, instance=request.user.userprofile)
            if form.is_valid():
                form.save()
            return redirect('/user/profile')  # Change 'profile' to your actual profile page URL
        elif form_name == 'bio':
            allowed_fields = ('first_name', 'last_name')
            post_data = {key: request.POST[key] for key in allowed_fields}
            form = UserBioChangeForm(post_data, instance=request.user)
            if form.is_valid():
                form.save()
            allowed_fields = ('gender', 'dob','bio')
            post_data = {key: request.POST[key].strip() for key in allowed_fields}
            form=UserBioChangeForm2(post_data, instance=request.user.userprofile)
            if form.is_valid():
                form.save()
            
        elif form_name == 'contact':
            post_data = {'email': request.POST['email']}
            form = EmailChange(post_data, instance=request.user)
            if form.is_valid():
                form.save()
            post_data = {'phone_number': request.POST['phone_number']}
            form = NumberChange(post_data, instance=request.user.userprofile)
            if form.is_valid():
                form.save()
    
    return redirect('/user/profile')

def validate_email(request):
    email = request.GET.get('email')
    is_taken = User.objects.filter(email=email).exists()
    return JsonResponse({'is_taken': is_taken})

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def cart_view(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # Use get_or_create to retrieve the user's shopping cart or create a new one
        shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user)

        cart_items = shopping_cart.items.all()
        total_price = shopping_cart.total_price
    else:
        cart_items = []  # If the user is not authenticated, display an empty cart
        total_price = 0
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'cart_item_count':cart_item_count,

    }    
    return render(request, 'user/cart.html', context)

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def purchase_history_view(request):
    # Get the user's purchase history
    purchase_history = PurchaseHistory.objects.filter(user=request.user).order_by('-purchase_date')
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    context = {
        'purchase_history': purchase_history,
        'cart_item_count':cart_item_count,

    }
    
    return render(request, 'user/purchase_history.html', context)

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def generate_receipt(request):
    if request.method == "POST":
        start_date_str = request.POST.get("start_date")
        end_date_str = request.POST.get("end_date")

        # Parse the start and end dates from the form
        start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

        # Query the purchase history for records within the specified date range
        purchase_history = PurchaseHistory.objects.filter(
            user=request.user,
            purchase_date__gte=start_date,
            purchase_date__lte=end_date
        ).order_by('-purchase_date')

        # Calculate the total_price of all orders within the date range
        total_price = Decimal(0)
        for history in purchase_history:
            total_price += history.total_price

        # Create a context for the receipt template
        context = {
            'purchase_history': purchase_history,
            'start_date': start_date,
            'end_date': end_date,
            'total_price': total_price,  # Pass the total_price to the template
        }

        # Render the receipt template to HTML
        template_name = 'user/receipt.html'
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="receipt_for_purchases_from_{start_date}_to_{end_date}.pdf"'

        buffer = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(render_to_string(template_name, context).encode("UTF-8")), buffer)
        
        if not pdf.err:
            response.write(buffer.getvalue())
            return response
        response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_for_purchases_from_{start_date}_to_{end_date}.pdf"'

    # Render the HTML template to PDF
    with open('user/receipt.html', 'r') as template_file:
        template_content = template_file.read()
        rendered_html = render(request, 'invoice.html', context)

        # Create a PDF using pisa
        pisa_status = pisa.CreatePDF(
            rendered_html.content,
            dest=response,
            link_callback=None  # Optional: Handle external links
        )
    return response

@login_required
def user_view(request,username):
    context={}
    user=User.objects.get(username=username)
    act=UserActivity.objects.get(user=user)
    if user:
        threshold = timezone.now() - timezone.timedelta(minutes=15)
        user_activity = UserActivity.objects.filter(user=user, last_activity__gte=threshold)
        if user_activity:
            status="Online"
        else:
            status="Offline"
        if act:
            profile = UserProfile.objects.get(user=user)
            purchase_history = PurchaseHistory.objects.filter(user=user)
            messages = Message.objects.filter(
                Q(sender=request.user, receiver=user) | Q(sender=user, receiver=request.user)
            ).order_by('timestamp')
            for message in reversed(messages):
                if message.receiver == request.user:
                    message.read_status = True
                    message.save()
                else:
                    break
            context = {
                'user_prof': user,
                'profile': profile,
                'is_author': profile.is_author,
                'total_money_spent': purchase_history.aggregate(total_price=Sum('total_price'))['total_price'] or 0,
                'gender': profile.gender,
                'books_bought':sum(history.items.count() for history in purchase_history),
                'dob': profile.dob,
                'last_activity':act.last_activity.strftime('%b. %d, %Y, %I:%M %p'),
                'status':status,
                'messages':messages
            }
            print(act.last_activity)
    return render(request, 'user/ext_prof.html',context)

@login_required
def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        receiver_username = data.get('receiver')
        content = data.get('content')
        message = Message.objects.create(sender=request.user, receiver=User.objects.get(username=receiver_username), content=content)
        message.create_notification()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def refresh_messages_view(request):
    last_timestamp = request.GET.get('last_timestamp')
    try:
        sender=User.objects.get(username=request.GET.get('username'))
    except:
        print("Unauthorised retrieval")
    if not last_timestamp:
        return JsonResponse({'error': 'Invalid last timestamp'}, status=400)
    # Convert the last_timestamp to a datetime object
    last_timestamp = timezone.datetime.fromisoformat(last_timestamp)

    # Retrieve new messages after last_timestamp
    new_messages = Message.objects.filter(
    receiver=request.user,
    sender=sender,
    timestamp__gte=last_timestamp + timedelta(seconds=1)
).order_by('timestamp')
    for message in new_messages:
        message.read_status = True
        message.save()
    # Serialize the new messages
    serialized_messages = []
    for message in new_messages:
        serialized_message = {
            'content': message.content,
            'sender': message.sender.username,
            'timestamp': message.timestamp.isoformat(),
        }
        serialized_messages.append(serialized_message)

    return JsonResponse({'messages': serialized_messages})

def clear_message_notification(request):
    if request.POST:
        usr=User.objects.get(username=request.POST.get('username'))
        notification_to_delete = Notification.objects.filter(
        recipient=request.user,
        sender=usr,
        notification_type=NotificationType.MESSAGE,
        is_read=False,
    ).first()  # Use first() to get the first matching notification or None
        if notification_to_delete:
            notification_to_delete.is_read=True
            notification_to_delete.save()
        return HttpResponse('ok')
        

# def register(request):
    # if request.method == 'POST':
    #     form = RegisterForm(request.POST)
    #     if form.is_valid():
    #         form.save()
    #         username = form.cleaned_data.get('username')
    #         email = form.cleaned_data.get('email')
    #         ######################### mail system ####################################
    #         htmly = get_template('user/Email.html')
    #         d = { 'username': username }
    #         subject, from_email, to = 'welcome', 'your_email@gmail.com', email
    #         html_content = htmly.render(d)
    #         msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
    #         msg.attach_alternative(html_content, "text/html")
    #         msg.send()
    #         ##################################################################
    #         messages.success(request, f'Your account has been created ! You are now able to log in')
    #         return redirect('login')
    # else:
    #     form = RegisterForm()
    # return render(request, 'user/register.html', {'form': form, 'title':'register here'})
    # return render(request, 'user/register.html')

# from django.shortcuts import render, redirect



# Create your views here.
# def register(response):
#     if response.method == "POST":
#         form = RegisterForm(response.POST)
#         if form.is_valid():
#             form.save()

#         return redirect("/home")
#     else:
#         form = RegisterForm()
#         return render(response, "register/register.html", {"form":form})

# def Signup(request):
#     global registered
#     global u1
#     registered=False
#     if(request.method=='POST'):
#         Member=Membr_form(request.POST,request.FILES)
#         if Member.is_valid():
#             user=Member.save()
#             username=request.POST.get('username','')
#             u1=username
#             password = request.POST.get('password','')
#             Email=request.POSt.get('email','')
#             cpassword=request.POST.get('cpass','')
#             user.save()
#             user=authenticate()
#             if user is None:
#                 user=get_user_model().objects.create_user(username=username,password=password,email=Email)
#                 user.save()
#             else:
#                 print("user_form.errors")
#             return redirect('/otp/')
#         else:
#             Member=Membr_form()
#             return render(request,'error.html')
