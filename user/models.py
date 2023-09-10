from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import User
# class Member(models.Model):
#     UserName=models.CharField(max_length=26)
#     Email=models.EmailField()
#     profile_pic=models.ImageField(upload_to='dp',blank=True)
#     def __str__(self):
#         return self.UserName
class OTPModel(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return self.expires_at > timezone.now()
    
    def __str__(self):
        return f"OTP for {self.user.username}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_author = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    gender = models.CharField(max_length=20, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    dob = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to='user/profile_images/', blank=True, null=True)

    def __str__(self):
        return self.user.username
    
