from django.shortcuts import render, redirect,get_object_or_404
from .forms import BookForm,CategoryForm,ReviewForm
from .models import Authors, Languages, Books,Category,Review
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
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
    paginator = Paginator(books, 8)
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

def book_detail(request, book_id):
    book = get_object_or_404(Books, pk=book_id)
    return render(request, 'books/book_detail.html', {'book': book})

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

def search_books(request):
    query = request.GET.get('query', '')
    limit = request.GET.get('limit', 0)
    if int(limit)>0:
        results = Books.objects.filter(Title__icontains=query)[:1]
    else:
        results = Books.objects.filter(Title__icontains=query)[:10]
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
                style_rating, story_rating, grammar_rating, character_rating, overall_rating = map(int, request.POST.get('Rating').split())
                review.style_rating = style_rating
                review.story_rating = story_rating
                review.grammar_rating = grammar_rating
                review.character_rating = character_rating
                review.overall_rating = overall_rating
                review.save()
                context = {'message': 'Review submitted successfully'}

            return redirect('book_detail', book_id)

    context = {'message': 'Oops... Something went wrong'}
    return redirect('book_detail', book_id)