from django.urls import path
from . import views
from .views import CustomPasswordResetView
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetDoneView,PasswordResetCompleteView
urlpatterns = [
    path('login/',views.login,name='login'),
    path('home/',views.home,name="home"),
    path('register/',views.register,name='register'),
    path('reset/',CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('validate-username/', views.validate_username, name='validate_username'),
    path('profile/', views.user_profile, name='user_profile'),
    path('save_user/', views.save_profile, name='save_user'),
    path('save_bio/', views.save_profile, name='save_bio'),
    path('save_contact/', views.save_profile, name='save_contact'),
]
