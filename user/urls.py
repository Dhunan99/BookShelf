from django.urls import path
from . import views
from .views import CustomPasswordResetView
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetDoneView,PasswordResetCompleteView
urlpatterns = [
    path('login/',views.login,name='login'),
    path('home/',views.home),
    path('register/',views.register,name='register'),
    path('reset/',CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
]
