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
from .models import OTPModel
from pyotp import TOTP
from django.http import JsonResponse
import secrets
from django.core.mail import send_mail
from books.models import Books
from django.views.decorators.csrf import csrf_exempt
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
    context = {
        'books': books,
    }
    return render(request,'user/home.html',context)

@login_required
def user_profile(request):
     return render(request,'user/profile.html')

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
