from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
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
    
