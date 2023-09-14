from django.shortcuts import render, redirect,get_object_or_404
from .forms import BookForm,CategoryForm,ReviewForm
from .models import Authors, Languages, Books,Category,Review,Like
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse,HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.contrib.auth.decorators import login_required
from user.models import UserProfile
# Create your views here.
def user_is_superuser(user):
    return user.is_superuser
@user_passes_test(user_is_superuser)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST,request.FILES)
        if form.is_valid():
            # Create or get the Author instance
            author_name = form.cleaned_data['author_name']
            author, created = Authors.objects.get_or_create(AuthorName=author_name)

            # Create or get the Language instance
            language_name = form.cleaned_data['language_name']
            language, created = Languages.objects.get_or_create(LanguageName=language_name)

            # Create the Book instance
            book = Books.objects.create(
                Title=form.cleaned_data['title'],
                Author=author,
                ISBN=form.cleaned_data['isbn'],
                PublicationYear=form.cleaned_data['Publication_Year'],
                Description=form.cleaned_data['description'],
                LanguageID=language,
                Price=form.cleaned_data['price'],
                cover_image = form.cleaned_data['cover_image']
            )
            cat = form.cleaned_data['categories']
            book.Categories.set(cat)
            return render(request,'books/book_added.html')  # Redirect to a success page

    else:
        form = BookForm()
    categories = Category.objects.all()
    return render(request, 'books/add_book.html', {'form': form, 'categories': categories})

def book_list(request):
    books = Books.objects.all()
    categories=Category.objects.all()
    paginator = Paginator(books, 6)
    page = request.GET.get('page')
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)
    context={
        'books':current_page,
        'categories':categories
    }
    return render(request, 'books/book_list.html', context)

def book_list_by_category(request, category):
    category_obj = get_object_or_404(Category, name=category)
    books = Books.objects.filter(Categories=category_obj)
    categories = Category.objects.all()
    paginator = Paginator(books, 8)
    page = request.GET.get('page')
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)
    context = {
        'books': current_page,
        'categories': categories
    }
    return render(request, 'books/book_list.html', context)

def book_detail(request, book_id, form=None):
    book = get_object_or_404(Books, pk=book_id)
    user = request.user

    # Check if the book is in the user's library
    user_library, created = UserLibrary.objects.get_or_create(user=user)
    book_in_library = book in user_library.books.all()

    # Retrieve user review and liked reviews
    user_review = Review.objects.filter(book=book, user=user).first()
    reviews = Review.objects.filter(book=book)
    liked_reviews = Like.objects.filter(user=user).values_list('review_id', flat=True)
    liked_reviews_set = set(liked_reviews)

    profile_image_urls = {}

    for review in reviews:
        reviewer = review.user
        user_profile = UserProfile.objects.get(user=reviewer)
        profile_image_urls[reviewer.username] = user_profile.profile_image.url if user_profile.profile_image else None

        if review.id in liked_reviews_set:
            review.is_liked = True
        else:
            review.is_liked = False


    return render(request, 'books/book_detail.html', {
        'book': book,
        'form': form,
        'user_review': user_review,
        'reviews': reviews,
        'book_in_library': book_in_library,
        'profile_image_urls': profile_image_urls,  
    })

@user_passes_test(user_is_superuser)
def delete_book(request, book_id): 
    book = get_object_or_404(Books, pk=book_id)
    if request.method == 'POST':
        book.delete()
        return redirect('/books/book_list')  # Redirect to your books list page
    return render(request, 'books/delete_book.html', {'book': book})

@user_passes_test(user_is_superuser)
def add_category(request):
    info=''
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            try:
                Category.objects.create(name=name)
                info='Category Added!'
            except IntegrityError as e:
                form.add_error('name', 'This value already exists. Please choose a unique value.')
    else:
        form = CategoryForm()
    return render(request, 'books/add_category.html', {'form': form,'info':info})

from django.http import JsonResponse
from .models import Books, UserLibrary

def search_books(request):
    query = request.GET.get('query', '')
    library = request.GET.get('library', None)
    limit = int(request.GET.get('limit', 10))

    if library is not None:
        # Search in the user's library
        user_library = UserLibrary.objects.get_or_create(user=request.user)[0]
        results = user_library.books.filter(Title__icontains=query)[:limit]
    else:
        # Search in all books
        results = Books.objects.filter(Title__icontains=query)[:limit]

    data = []
    for book in results:
        book_data = {
            'id': book.BookID,
            'title': book.Title,
            'cover_url': book.cover_image.url if book.cover_image else '',
        }
        data.append(book_data)

    return JsonResponse(data, safe=False)


def add_review(request, book_id):
    book = Books.objects.get(pk=book_id)
    user = request.user

    # Check if a review by the current user for the specified book already exists
    existing_review = Review.objects.filter(book=book, user=user).first()

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # Create a new review object or update an existing one
            if existing_review:
                review = form.save(commit=False)
                existing_review.title = review.title
                existing_review.review = review.review
                existing_review.style_rating, existing_review.story_rating, existing_review.grammar_rating, existing_review.character_rating,existing_review.overall_rating = map(float, request.POST.get('Rating').split())
                existing_review.save()
                context = {'message': 'Review updated successfully'}
            else:
                review = form.save(commit=False)
                review.book = book
                review.user = user
                style_rating, story_rating, grammar_rating, character_rating, overall_rating = map(float, request.POST.get('Rating').split())
                review.style_rating = style_rating
                review.story_rating = story_rating
                review.grammar_rating = grammar_rating
                review.character_rating = character_rating
                review.overall_rating = overall_rating
                review.save()
                context = {'message': 'Review submitted successfully'}
            book.calculate_average_rating()
            return redirect('book_detail', book_id)
        else:
            a=book_detail(request, book_id=book_id,form=form)
            return a
            
    context = {'message': 'Oops... Something went wrong'}
    return redirect('book_detail', book_id)

def toggle_like_review(request):
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        user = request.user

        try:
            # Check if the user has already liked the review
            like = Like.objects.get(user=user, review=review)
            # If the like exists, remove it (unlike)
            like.delete()
            review.update_likes_count()
            return HttpResponse("Unliked successfully")
        except Like.DoesNotExist:
            # If the like doesn't exist, create it (like)
            Like.objects.create(user=user, review=review)
            review.update_likes_count()
            return HttpResponse("Liked successfully")

    # Default response in case of invalid request or other conditions
    return HttpResponse("Invalid request")
    # Redirect or return a response as needed

def delete_review(request, review_id):
    # Get the review object to be deleted
    if request.POST:
        review = get_object_or_404(Review, pk=review_id)
        book = review.book

        # Check if the user is the owner of the review
        if review.user == request.user:
            review.delete()
            book.calculate_average_rating()
        return HttpResponse('refresh')

from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger
from .models import UserLibrary

def user_library(request):
    # Get the UserLibrary object for the currently logged-in user
    user_library, created = UserLibrary.objects.get_or_create(user=request.user)

    # Get the books in the user's library
    user_library_books = user_library.books.all()

    categories = Category.objects.all()
    paginator = Paginator(user_library_books, 8)
    page = request.GET.get('page')

    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)

    context = {
        'books': current_page,
        'categories': categories
    }

    return render(request, 'books/user_library.html', context)

def user_library_category(request, category):
    category_obj = get_object_or_404(Category, name=category)
    
    # Get the UserLibrary object for the currently logged-in user
    user_library, created = UserLibrary.objects.get_or_create(user=request.user)

    # Filter books by category and user's library
    books = Books.objects.filter(Categories=category_obj, userlibrary=user_library)

    categories = Category.objects.all()
    paginator = Paginator(books, 6)
    page = request.GET.get('page')
    
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)
    
    context = {
        'books': current_page,
        'categories': categories
    }
    return render(request, 'books/user_library.html', context)

def add_to_library(request, book_id):
    book = get_object_or_404(Books, pk=book_id)
    user_library, created = UserLibrary.objects.get_or_create(user=request.user)
    if book not in user_library.books.all():
        user_library.books.add(book)
    return redirect(f'/books/book/{book_id}')

from django.db.models import Q

@login_required
def filter_books(request):
    query = request.GET.get('query', '')
    user = request.user

    # Get the user's library
    user_library, created = UserLibrary.objects.get_or_create(user=user)

    # Filter the user's library books based on the query
    user_library_books = user_library.books.filter(
        Q(Title__icontains=query) | Q(Author__AuthorName__icontains=query)
    ).distinct()

    # Convert the user_library_books queryset to a list of dictionaries
    user_library_books_list = [
        {
            'BookID': book.BookID,
            'Title': book.Title,
            'Author__AuthorName': book.Author.AuthorName,
            'Categories__name': [category.name for category in book.Categories.all()],
            'Price': book.Price,
            'cover_image': book.cover_image.url if book.cover_image else None,
            'language':book.LanguageID.LanguageName
        }
        for book in user_library_books
    ]

    return JsonResponse(user_library_books_list, safe=False)

def author_list(request):
    authors = Authors.objects.all()

    # Set the number of authors to display per page
    paginator = Paginator(authors, 6)
    page = request.GET.get('page')

    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)

    return render(request, 'books/author_list.html', {'authors': current_page})

def view_works(request, author_id,category=None):
    # Retrieve the author based on the author_id
    author = get_object_or_404(Authors, pk=author_id)

    # Retrieve the author's works (you'll need to adjust this based on your models)
    if category is not None:
        books = Books.objects.filter(Categories__name=category, Author=author)
    else:
        books = author.books_set.all()
    categories = Category.objects.all()
    paginator = Paginator(books, 6)
    page = request.GET.get('page')
    
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)

    # Render a template with the works
    return render(request, 'books/author_books.html', {'author': author, 'books': current_page,'categories':categories})

from django.core.exceptions import ObjectDoesNotExist

def filter_books_by_author(request):
    author_id = request.GET.get('author_id', '')
    query = request.GET.get('query', '')

    try:
        author_id = int(author_id)
        author = Authors.objects.get(Author=author_id)

        # Filter books by author's ID and book title
        books_by_author_and_title = Books.objects.filter(
            Q(Author=author) &
            Q(Title__icontains=query)
        ).distinct()

        # Convert the books_by_author_and_title queryset to a list of dictionaries
        books_by_author_and_title_list = [
            {
                'BookID': book.BookID,
                'Title': book.Title,
                'Author__AuthorName': book.Author.AuthorName,
                'Categories__name': [category.name for category in book.Categories.all()],
                'Price': book.Price,
                'cover_image': book.cover_image.url if book.cover_image else None,
                'language': book.LanguageID.LanguageName
            }
            for book in books_by_author_and_title
        ]

        return JsonResponse(books_by_author_and_title_list, safe=False)

    except ObjectDoesNotExist:
        # Handle the case where the author with the provided ID doesn't exist
        return JsonResponse([], safe=False)

