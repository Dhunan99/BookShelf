from django.urls import path
from . import views
urlpatterns = [
path('pay/', views.paymenthandler, name='paymenthandler'),
path('home/<int:book_id>/',views.homepage,name='pay_home'),
path('checkout/', views.checkout, name='checkout'),
]
