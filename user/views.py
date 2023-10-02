from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import login as lg, authenticate
from django.contrib.auth.models import User
from .forms import NewUserForm,UserBioChangeForm,CustomUserChangeForm,UserBioChangeForm2,EmailChange,NumberChange,UserProfileChangeForm
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib.auth.models import User
from .models import OTPModel,ShoppingCart,PurchaseHistory,Notification
from pyotp import TOTP
from django.http import JsonResponse
import secrets
from django.core.mail import send_mail
from django.contrib.auth.views import PasswordChangeView
from books.models import Books
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string

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
                    return redirect('/user/home')
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


@login_required
def home(request):
     # Fetch book data from the Books model
    books = Books.objects.filter(tags__name='Popular')  # You can also filter or order the data as needed
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
            allowed_fields = ('gender', 'dob')
            post_data = {key: request.POST[key] for key in allowed_fields}
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
