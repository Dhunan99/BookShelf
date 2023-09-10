from django.urls import path
from . import views
urlpatterns = [
    path('add_book',views.add_book),
    path('book_list/', views.book_list, name='book_list'),
    path('delete/<int:book_id>/', views.delete_book, name='delete_book'),
    path('add_category/', views.add_category, name='add_category'),
    path('book_list/<str:category>/', views.book_list_by_category, name='book_list_by_category'),
    path('search/', views.search_books, name='search_books'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('add_review/<int:book_id>/', views.add_review, name='add_review'),
]