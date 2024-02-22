from django.urls import path
from . import views
from .views import CustomPasswordResetView,CustomPasswordResetDoneView
from django.contrib.auth.views import PasswordResetConfirmView,PasswordResetCompleteView
urlpatterns = [
    path('login/',views.login,name='login'),
    path('home/',views.home,name="home"),
    path('register/',views.register,name='register'),
    path('reset/',CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('validate-username/', views.validate_username, name='validate_username'),
    path('validate-email/', views.validate_email, name='validate_email'),
    path('profile/', views.user_profile, name='user_profile'),
    path('save_user/', views.save_profile, name='save_user'),
    path('save_bio/', views.save_profile, name='save_bio'),
    path('save_contact/', views.save_profile, name='save_contact'),
    path('change_password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('cart/', views.cart_view, name='cart_view'),
    path('purchase-history/', views.purchase_history_view, name='purchase_history'),
    path('get-notifications/',views.notifications_view,name="notifications_view"),
    path('mark-notifications-as-read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),
    path('generate-receipt/', views.generate_receipt, name='generate_receipt'),
    path('user_view/<str:username>',views.user_view, name="user_view"),
    path('send_message/', views.send_message, name='send_message'),
    path('refresh_messages/', views.refresh_messages_view, name='refresh_messages'),
    path('clear_message_notification',views.clear_message_notification,name='clear_message_notification')
]
