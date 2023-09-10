from django.contrib.auth.forms import UserCreationForm,UserChangeForm
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserProfile

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

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'gender', 'dob', 'phone_number']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username',)

class UserProfileChangeForm(UserChangeForm):
    class Meta:
        model = UserProfile
        fields = ('profile_image',)

class UserBioChangeForm(UserChangeForm):
	class Meta:
		model=User
		fields=('first_name','last_name',)

class UserBioChangeForm2(UserChangeForm):
	class Meta:
		model=UserProfile
		fields=('gender','dob',)

class EmailChange(UserChangeForm):
	class Meta:
		model=User
		fields=('email',)

class NumberChange(UserChangeForm):
	class Meta:
		model=UserProfile
		fields=('phone_number',)



#  from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User


# class RegisterForm(UserCreationForm):
#     email = forms.EmailField()

#     class Meta:
#         model = User
#         fields = ["username", "email", "password1", "password2"]
