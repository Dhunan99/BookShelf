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
    path('like/', views.toggle_like_review, name='toggle_like_review'),
    path('delete_review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('user_library/', views.user_library, name='user_library'),
    path('user_library/<str:category>/', views.user_library_category, name='user_library_category'),
    path('add_to_library/<int:book_id>/', views.add_to_library, name='add_to_library'),
    path('filter_books/', views.filter_books, name='filter_books'),
    path('authors/', views.author_list, name='author_list'),
    path('author_works/<int:author_id>/', views.view_works, name='view_works'),
    path('author_works/<int:author_id>/<str:category>/', views.view_works, name='view_works'),
    path('filter_books_by_author/', views.filter_books_by_author, name='filter_books_by_author'),
    path('<int:book_id>/chapter/<path:chapter_number>/', views.chapter_view, name='chapter_view'),
    path('add_to_cart/<int:book_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:book_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('report-review/', views.report_review, name='report_review'),
    path('reports/', views.report_list, name='report_list'),
    path('dismiss_report/', views.dismiss_report, name='dismiss_report'),
    path('delete_review_2/', views.delete_review_2, name='delete_review_2'),
    path('update_reading_progress/', views.update_reading_progress, name='update_reading_progress'),
    path('vote/', views.vote_endpoint, name='vote_endpoint'),
    path('ranking/<str:type>/', views.ranking, name='ranking'),
    path('ranking/', views.ranking, name='ranking'),



]