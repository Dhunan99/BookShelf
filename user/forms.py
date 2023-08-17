from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class NewUserForm(UserCreationForm):
	email = forms.EmailField(required=True)
	otp_verified = forms.BooleanField(required=False)
	class Meta:
		model = User
		fields = ("username", "email", "password1", "password2",) + ('otp_verified',)

	def clean_email(self):
			email = self.cleaned_data['email']
			if User.objects.filter(email=email).exists():
				raise forms.ValidationError('This email address is already in use.')
			return email
	
	def save(self, commit=True):
		user = super(NewUserForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user


#  from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User


# class RegisterForm(UserCreationForm):
#     email = forms.EmailField()

#     class Meta:
#         model = User
#         fields = ["username", "email", "password1", "password2"]
