# Register your models here.
from django.contrib import admin
from .models import UserProfile

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'gender', 'dob')
    list_filter = ('gender',)
    search_fields = ('user__username', 'user__email')

# Register the UserProfile model with the admin site
admin.site.register(UserProfile, UserProfileAdmin)
