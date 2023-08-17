from django.urls import path
from . import views
urlpatterns = [
    path('add_book',views.add_book),
    path('book_list/', views.book_list, name='book_list'),
    path('delete/<int:book_id>/', views.delete_book, name='delete_book'),
]