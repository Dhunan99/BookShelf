from django.shortcuts import render, redirect,get_object_or_404
from .forms import BookForm,CategoryForm,ReviewForm,BookFilterForm
from .models import Authors, Languages, Books,Category,Review,Like,Report,Vote,Post,ViewPost,LikePost,Reply
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import IntegrityError
from django.http import JsonResponse,HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.contrib.auth.decorators import login_required
from user.models import UserProfile,ShoppingCart,PurchaseHistory,ReadingProgress
from payment.models import Order
import ebooklib
from django.urls import reverse
from ebooklib import epub
import json
from datetime import datetime,date
from django.core.cache import cache
from django.http import Http404
from django.utils import timezone
from django.db import models
from itertools import chain
from .models import Folder,UserBook
from urllib.parse import urlparse
from .models import SocialMediaLink,Chapter

# Create your views here.
def user_is_superuser(user):
    return user.is_superuser

@user_passes_test(user_is_superuser)
def delete_review_2(request):
    if request.method == 'POST':
        review_id = request.POST.get('review_id')
        try:
            review = Review.objects.get(id=review_id)
            # Check if the user has permission to delete the review (you can customize this)
            if request.user.has_perm('your_app_name.can_delete_review'):
                review.delete()
                response_data = {'message': 'Review deleted successfully.'}
                return JsonResponse(response_data)
            else:
                response_data = {'error': 'Permission denied.'}
                return JsonResponse(response_data, status=403)  # Return a 403 Forbidden status
        except Review.DoesNotExist:
            response_data = {'error': 'Review not found.'}
            return JsonResponse(response_data, status=404)  # Return a 404 Not Found status

    # Handle other HTTP methods if needed
    return JsonResponse({'error': 'Invalid request method.'}, status=405)  # Return a 405 Method Not Allowed status

@user_passes_test(user_is_superuser)
def dismiss_report(request):
    try:
        report_id = request.POST.get('report_id')
        report = Report.objects.get(id=report_id)
        if request.user.has_perm('books.can_dismiss_report'):  
            report.dismissed = True
            report.save()
            response_data = {'message': 'Report dismissed successfully.'}
            return JsonResponse(response_data)
        else:
            response_data = {'error': 'Permission denied.'}
            return JsonResponse(response_data, status=403)  # Return a 403 Forbidden status

    except Report.DoesNotExist:
        response_data = {'error': 'Report not found.'}
        return JsonResponse(response_data, status=404)

@user_passes_test(user_is_superuser)
def report_list(request):
    # Query the reports, you can filter by dismissed=False to get pending reports
    reports = Report.objects.filter(dismissed=False)
    return render(request, 'books/review_review.html', {'reports': reports})

@require_POST
def report_review(request):
    # Get the user who is reporting the review
    user = request.user
    # Get the review ID and reason from the POST data
    review_id = request.POST.get('review_id')
    reason = request.POST.get('reason')
    print(review_id,reason)
    # Check if a report with the same user and review already exists
    existing_report = Report.objects.filter(user=user, review_id=review_id).first()

    if existing_report:
        # Report already exists, return an error response
        response_data = {'error': 'You have already reported this review.'}
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=400)

    # Create a new report entry
    report = Report(user=user, review_id=review_id, reason=reason)
    report.save()

    # Return a success response
    response_data = {'message': 'Report submitted successfully.'}
    return HttpResponse(json.dumps(response_data), content_type='application/json')

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

def extract_filter_params(request):
    filter_params = {
        'keyword': request.GET.get('keyword'),
        'author_name': request.GET.get('author_name'),
        'categories': request.GET.getlist('categories'),
        'sort_by': request.GET.get('sort_by'),
        'min_publication_year': request.GET.get('min_publication_year'),
        'max_publication_year': request.GET.get('max_publication_year'),
        'language': request.GET.get('language'),
        'min_review_count': request.GET.get('min_review_count'),
        'min_rating_value': request.GET.get('min_rating_value'),
        'sort_order':request.GET.get('sort_order')
    }
    return filter_params

def advanced_search(books, filter_params):
    keyword = filter_params['keyword']
    author_name = filter_params['author_name']
    categories = filter_params['categories']
    sort_by = filter_params['sort_by']
    sort_order = filter_params['sort_order']
    min_publication_year = filter_params['min_publication_year']
    max_publication_year = filter_params['max_publication_year']
    language = filter_params['language']
    min_review_count = filter_params['min_review_count']
    min_rating_value = filter_params['min_rating_value']

    # Create a Q object to build the filter conditions
    filter_conditions = Q()

    if keyword:
        filter_conditions &= Q(Title__icontains=keyword)

    if author_name:
        filter_conditions &= Q(Author__AuthorName__icontains=author_name)

    if categories:
        category_conditions = Q()
        for category in categories:
            category_conditions |= Q(Categories__name=category)
        filter_conditions &= category_conditions


    if min_publication_year:
        filter_conditions &= Q(PublicationYear__gte=min_publication_year)

    if max_publication_year:
        filter_conditions &= Q(PublicationYear__lte=max_publication_year)

    if language:
        filter_conditions &= Q(LanguageID__LanguageName=language)

    if min_review_count:
        filter_conditions &= Q(rating_count__gte=min_review_count)

    if min_rating_value:
        filter_conditions &= Q(rating__gte=min_rating_value)

    if sort_by == 'alphabetic':
        if sort_order == 'asc':
            books = books.order_by('Title')
        elif sort_order == 'desc':
            books = books.order_by('-Title')
    elif sort_by == 'price':
        if sort_order == 'asc':
            books = books.order_by('Price')
        elif sort_order == 'desc':
            books = books.order_by('-Price')

    filtered_books = books.filter(filter_conditions).distinct()

    return filtered_books


@login_required
def book_list(request):
    books = Books.objects.all()
    categories = Category.objects.all()
    languages=Languages.objects.all()
    items_per_page = request.GET.get('items_per_page', 6)
    filter_params = extract_filter_params(request)

    if (
        'keyword' in request.GET or
        'author_name' in request.GET or
        'categories' in request.GET or
        'sort_by' in request.GET or
        'min_publication_year' in request.GET or
        'max_publication_year' in request.GET or
        'language' in request.GET or
        'min_review_count' in request.GET or
        'min_rating_value' in request.GET
    ):
        # Call the filter_books function to filter the books
        books = advanced_search(books,filter_params)
    else:
        # No relevant GET parameters, use all books
        books = books
    books_v2 = []
    for book in books:
        in_library = book_in_user_library(book, request.user)
        in_cart= book_in_cart(book,request.user)
        book_data = {
            'book': book,
            'in_library': in_library,
            'in_cart':in_cart,
        }
        books_v2.append(book_data)
    paginator = Paginator(books_v2, items_per_page)
    page = request.GET.get('page',1)
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        current_page = paginator.page(1)
    except EmptyPage:
        current_page = paginator.page(paginator.num_pages) 
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    # Create a list to store books with the 'in_library' attribute

    context = {
        'books': current_page,  # Pass the new list to the template
        'categories': categories,
        'languages':languages,
        'items_per_page': items_per_page,
        'cart_item_count':cart_item_count,
        'keyword': filter_params['keyword'],
        'author_name': filter_params['author_name'],
        'sort_by': filter_params['sort_by'],
        'min_publication_year': filter_params['min_publication_year'],
        'max_publication_year': filter_params['max_publication_year'],
        'language': filter_params['language'],
        'min_review_count': filter_params['min_review_count'],
        'min_rating_value': filter_params['min_rating_value'],
        'categories_2':filter_params['categories'],
        'sort_order':filter_params['sort_order']
    }
    return render(request, 'books/book_list.html', context)

def book_in_cart(book, user):
    if user.is_authenticated:
        # Assuming your Book model has a ForeignKey to ShoppingCart named 'cart'
        return user.shopping_carts.filter(items=book).exists() 
    return False

@login_required
def book_list_by_category(request, category):
    category_obj = get_object_or_404(Category, name=category)
    books = Books.objects.filter(Categories=category_obj)
    categories = Category.objects.all()
    items_per_page = request.GET.get('items_per_page', 6)
    books_v2 = []
    for book in books:
        in_cart= book_in_cart(book,request.user)
        in_library = book_in_user_library(book, request.user)
        book_data = {
            'book': book,
            'in_library': in_library,
            'in_cart':in_cart,
        }
        books_v2.append(book_data)
    paginator = Paginator(books_v2, items_per_page)
    page = request.GET.get('page')
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range    
        current_page = paginator.page(1)
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    context = {
        'books': current_page,
        'categories': categories,
        'category':category,
        'items_per_page': items_per_page,
        'cart_item_count':cart_item_count,

    }
    return render(request, 'books/book_list.html', context)

@login_required
def extract_chapters_from_epub(request, book_id, limit=None):
    try:
        book = get_object_or_404(Books, pk=book_id)

        if book.epub_file:
            book_content = book.epub_file.path
            ebook = epub.read_epub(book_content)

            chapters = []

            for item in ebook.get_items():
                if item.get_type() == ebooklib.ITEM_NAVIGATION:
                    toc_content = item.get_content().decode('utf-8')
                    soup = BeautifulSoup(toc_content, 'html.parser')

                    for navpoint in soup.find_all('navpoint'):
                        title = navpoint.navlabel.text.strip()
                        href = navpoint.content['src'].strip()

                        if title and href:
                            href = href.split('.xhtml', 1)[0] + '.xhtml'
                            chapter_url = reverse('chapter_view', args=[book_id, href])
                            chapter_content = ebook.get_item_with_href(href)

                            if len(chapter_content.content.decode('utf-8')) > 900:
                                chapters.append({'title': title, 'url': chapter_url})

                            # Check if limit is reached and break loop if needed
                            if limit is not None and len(chapters) >= limit:
                                break
                    
                    # Check if limit is reached and break loop if needed
                    if limit is not None and len(chapters) >= limit:
                        break
                    
            return chapters


    except Exception as e:
        return render(request, 'books/error.html', {'error_message': str(e)})

@login_required
def book_detail(request, book_id, form=None):
    trigger=request.GET.get('chapter_list',None)
    trigger2=request.GET.get('preview')
    toggle=True if trigger is not None or trigger2 is not None else None
    book = get_object_or_404(Books, pk=book_id)
    user = request.user
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
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    try:
        reading_progress = ReadingProgress.objects.get(user=user, book=book)
    except ReadingProgress.DoesNotExist:
        # Handle the case where the reading progress object does not exist
        reading_progress = None
    if Vote.has_user_voted_today(user):
        voted=True
    else:
        voted=False
    context={
        'book': book,
        'form': form,
        'user_review': user_review,
        'reviews': reviews,
        'book_in_library': book_in_library,
        'in_cart':book_in_cart(book,request.user),
        'profile_image_urls': profile_image_urls,  
        'cart_item_count':cart_item_count,
        'reading_progress':reading_progress.current_url if reading_progress else None,
        'voted': voted,
        'toggle':toggle
    }
    if trigger == "True":
        if book.isOriginal==True:
            chapters = Chapter.objects.filter(book=book)
            chapter_list = []
            for chapter in chapters:
                chapter_data = {
                    'url': chapter.chapter_number,
                    'title': f"Ch. {chapter.chapter_number}. "+chapter.chapter_title
                }
                chapter_list.append(chapter_data)
            context['chapters'] = chapter_list
        else:
            context['chapters'] = extract_chapters_from_epub(request,book_id)
    elif trigger2=="True":
        if book.isOriginal==True:
            chapters = Chapter.objects.filter(book=book)
            chapter_list = []
            for chapter in chapters:
                chapter_data = {
                    'url': chapter.chapter_number,
                    'title': f"Ch. {chapter.chapter_number} - "+chapter.chapter_title
                }
                chapter_list.append(chapter_data)
            context['chapters'] = chapter_list[:8]
            context['preview']=True
        else:
            context['chapters'] = extract_chapters_from_epub(request,book_id,limit=8)
            context['preview']=True
    return render(request, 'books/book_detail.html', context)

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

@login_required
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
def remove_from_cart(request, book_id):
    # Get the book object based on the book_id
    book = get_object_or_404(Books, pk=book_id)

    # Check if the user is authenticated
    if request.user.is_authenticated:
        try:
            # Try to get the user's shopping cart
            shopping_cart = ShoppingCart.objects.get(user=request.user)
        except ShoppingCart.DoesNotExist:
            # If the cart doesn't exist, create a new one
            shopping_cart = ShoppingCart(user=request.user)
            shopping_cart.save()

        # Remove the book from the cart's items
        shopping_cart.items.remove(book)
        shopping_cart.update_total_price()

    # Redirect back to the cart page
    return redirect('cart_view')

@login_required
def add_review(request, book_id):
    ok=UserLibrary.objects.filter(user=request.user).first()
    book = Books.objects.get(pk=book_id)
    if book in ok.books.all():
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
                    existing_review.calculate_sentiment_score()
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
                    review.calculate_sentiment_score()
                    review.save()
                    context = {'message': 'Review submitted successfully'}
                book.calculate_average_rating()
                return redirect('book_detail', book_id)
            else:
                a=book_detail(request, book_id=book_id,form=form)
                return a
                
        context = {'message': 'Oops... Something went wrong'}
    else:
        return HttpResponse("Not Allowed")

    return redirect('book_detail', book_id)

@login_required
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

@login_required
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

@login_required
def user_library(request):
    # Get the UserLibrary object for the currently logged-in user
    user_library, created = UserLibrary.objects.get_or_create(user=request.user)
    folder=request.GET.get('folders', 'all')
    book_ids=None
    if folder!='all':
        folder=Folder.objects.get(name=folder,user_library=user_library)
        user_books_in_folder_with_books = UserBook.objects.filter(folder=folder).select_related('book').values('book').distinct()
        book_ids = [item['book'] for item in user_books_in_folder_with_books]
        user_library_books = user_library.books.filter(pk__in=book_ids)
    else:
        user_library_books = user_library.books.all()
    items_per_page = request.GET.get('items_per_page', 6)
    categories = Category.objects.all()
    paginator = Paginator(user_library_books, items_per_page)
    page = request.GET.get('page')

    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
        cart_item_count = 0
    folders=Folder.objects.filter(user_library=user_library)
    user_books = UserBook.objects.filter(folder__user_library=user_library)
    for book in current_page:
        try:
            # Try to get the assigned folder for the book
            assigned_folder = user_books.get(book_id=book.BookID).folder.name
        except UserBook.DoesNotExist:
            # Handle the case where the book is not assigned to any folder
            assigned_folder = None
    # Add the assigned folder name to the book object
        book.folder = assigned_folder
    context = {
        'books': current_page,
        'categories': categories,
        'items_per_page':items_per_page,
        'cart_item_count':cart_item_count,
        'folders':folders,
        'selected_folder':folder,
        'arranged_books':user_books,
    }
    return render(request, 'books/user_library.html', context)

@login_required
def user_library_category(request, category):
    category_obj = get_object_or_404(Category, name=category)
    
    # Get the UserLibrary object for the currently logged-in user
    user_library, created = UserLibrary.objects.get_or_create(user=request.user)

    # Filter books by category and user's library
    books = Books.objects.filter(Categories=category_obj, userlibrary=user_library)
    items_per_page = request.GET.get('items_per_page', 6)
    categories = Category.objects.all()
    paginator = Paginator(books, items_per_page)
    page = request.GET.get('page')
    
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    context = {
        'books': current_page,
        'categories': categories,
        'category':category,
        'items_per_page':items_per_page,
        'cart_item_count':cart_item_count,

    }
    return render(request, 'books/user_library.html', context)

def add_to_library(user, book_id,alt=False,order1=None):
    book = get_object_or_404(Books, pk=book_id)
    user_library, created = UserLibrary.objects.get_or_create(user=user)
    cart=ShoppingCart.objects.get_or_create(user=user)
    if book not in user_library.books.all():
        user_library.books.add(book)
        
        if alt==False:
            purchase_history = PurchaseHistory.objects.create(
                user=user,
                total_price=book.Price,
                purchase_date=datetime.now(),
                order=order1
            )
            # Add the purchased book to the purchase history
            purchase_history.items.add(book)
            purchase_history.save()
    
    if alt==False:
        if book in cart[0].items.all():
            cart[0].items.remove(book)
    
    return None


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

@login_required
def author_list(request):
    authors = Authors.objects.all()
    items_per_page = request.GET.get('items_per_page', 6)

    # Set the number of authors to display per page
    paginator = Paginator(authors, items_per_page)
    page = request.GET.get('page')

    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    return render(request, 'books/author_list.html', {'authors': current_page,'items_per_page': items_per_page,'cart_item_count':cart_item_count,})

@login_required
def view_works(request, author_id,category=None):
    # Retrieve the author based on the author_id
    author = get_object_or_404(Authors, pk=author_id)
    items_per_page = request.GET.get('items_per_page', 6)
    # Retrieve the author's works (you'll need to adjust this based on your models)
    if category is not None:
        books = Books.objects.filter(Categories__name=category, Author=author)
    else:
        books = author.books_set.all()
    books_v2 = []
    for book in books:
        in_cart= book_in_cart(book,request.user)
        in_library = book_in_user_library(book, request.user)
        book_data = {
            'book': book,
            'in_library': in_library,
            'in_cart':in_cart,
        }
        books_v2.append(book_data)
    categories = Category.objects.all()
    paginator = Paginator(books_v2, items_per_page)
    page = request.GET.get('page')
    
    try:
        current_page = paginator.page(page)
    except PageNotAnInteger:
        # Handle the case where the page is out of range
        current_page = paginator.page(1)
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
            # If the user doesn't have a cart, set item count to 0
        cart_item_count = 0
    # Render a template with the works
    return render(request, 'books/author_books.html', {'author': author, 'books': current_page,'categories':categories,'items_per_page':items_per_page,'cart_item_count':cart_item_count})

from django.core.exceptions import ObjectDoesNotExist

@login_required
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
    
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def remove_images_from_soup(soup):
    # Find all image tags and remove them from the BeautifulSoup object
    for img_tag in soup.find_all('img'):
        img_tag.decompose()

@login_required
def chapter_view(request, book_id, chapter_number):
    # Retrieve the book based on the BookID
    book = get_object_or_404(Books, BookID=book_id)
    try:
        if book.epub_file:
            book_content = book.epub_file.path  # Read the content directly
            ebook = epub.read_epub(book_content)

            # Find the chapter by chapter_number
            chapter = None
            for doc in ebook.get_items_of_type(ebooklib.ITEM_DOCUMENT):

                # Extract the chapter number from the filename
                filename = doc.get_name()
                if filename == chapter_number:
                    chapter = doc
                    break

            if chapter:
                # Get the raw content of the chapter without decoding
                content_bytes = chapter.content

                # Decode the content from bytes to a Unicode string
                content_unicode = content_bytes.decode('utf-8')

                # Parse the HTML content with BeautifulSoup
                soup = BeautifulSoup(content_unicode, 'html.parser')
                # Remove images from the soup
                remove_images_from_soup(soup)

                # Get the modified content as a string
                modified_content = str(soup)

                # Extract chapters from the EPUB and find prev and next chapters
                lib=UserLibrary.objects.filter(user=request.user).first()
                if book in lib.books.all():
                    chapters = extract_chapters_from_epub(request, book_id)
                else:
                    chapters = extract_chapters_from_epub(request, book_id,limit=8)
                prev_chapter = None
                next_chapter = None
                for i in range(len(chapters)):
                    if chapter_number in chapters[i]['url']:
                        if i > 0:
                            prev_chapter = chapters[i - 1]
                        if i < len(chapters) - 1:
                            next_chapter = chapters[i + 1]
                # Pass the modified content, prev, and next chapters as context to your template
                user_cart = ShoppingCart.objects.filter(user=request.user).first()
                if user_cart:
                    cart_item_count = user_cart.items.count()
                else:
                        # If the user doesn't have a cart, set item count to 0
                    cart_item_count = 0
                context = {
                    'chapter_content': modified_content,
                    'book':book,
                    'chapter_type': chapter.get_type(),
                    'cart_item_count':cart_item_count,

                }
                if prev_chapter is not None:
                    context['prev_chapter'] = prev_chapter['url']

                if next_chapter is not None:
                    context['next_chapter'] = next_chapter['url']
                    
                return render(request, 'books/read.html', context)
                
            else:
                return render(request, 'books/error.html', {'error_message': 'Chapter not found.'})
        else:
            return render(request, 'books/error.html', {'error_message': 'No EPUB file associated with this book.'})

    except Exception as e:
        return render(request, 'books/error.html', {'error_message': str(e)})

def book_in_user_library(book, user):
    try:
        user_library = UserLibrary.objects.get(user=user)
    except UserLibrary.DoesNotExist:
        user_library = UserLibrary.objects.create(user=user)

    return book in user_library.books.all()

import re
def increment_last_number(chapter_number):
    # Split the string by numbers
    parts = re.split(r'(\d+)', chapter_number)

    if len(parts) >= 2:
        # Find the last number in the list and increment it
        last_number = int(parts[-2])
        incremented_number = str(last_number + 1)

        # Pad the incremented number with leading zeros to match the original format
        incremented_number = incremented_number.zfill(len(parts[-2]))

        # Replace the last number in the string with the incremented number
        parts[-2] = incremented_number

        # Recombine the string parts
        incremented_chapter_number = ''.join(parts)

        return incremented_chapter_number
    else:
        # If no numbers found, return the original string
        return chapter_number
    
def add_to_cart(request, book_id):
    book = get_object_or_404(Books, BookID=book_id)

    if request.user.is_authenticated:
        shopping_cart, created = ShoppingCart.objects.get_or_create(user=request.user)
        shopping_cart.items.add(book)
        shopping_cart.update_total_price()
        shopping_cart.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

def update_reading_progress(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        current_url = request.POST.get('current_url')

        user = request.user
        book = get_object_or_404(Books, pk=book_id)

        # Get or create a reading progress instance
        reading_progress, created = ReadingProgress.objects.get_or_create(user=user, book=book)

        # Update the current URL
        reading_progress.current_url = current_url

        reading_progress.save()

        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})
    
def vote_endpoint(request,type=None):
    data = json.loads(request.body)
    book_id = data.get('book_id')
    user = request.user  
    vote, created = Vote.objects.get_or_create(user=user, book_id=book_id, vote_date=timezone.now())

    if created:
        # Vote was successfully created
        return JsonResponse({'message': 'Vote successful'})
    else:
        # User has already voted for the book today
        return JsonResponse({'message': 'User has already voted for this book today'}, status=400)
    
@login_required
def ranking(request, type='alltime'):
    if type and type not in ('annual', 'weekly', 'monthly', 'daily', 'alltime'):
        raise Http404("This page does not exist")
    
    cache_key = f'ranking_{type}'
    cache_timestamp_key = f'ranking_{type}_timestamp'
    
    ranking_data = cache.get(cache_key)
    cache_timestamp = cache.get(cache_timestamp_key)
    
    # Check if the cache timestamp is older than 1 minute
    if cache_timestamp:
        time_difference = timezone.now() - cache_timestamp
        if time_difference.total_seconds() > 60:
            ranking_data = None  # Force recalculation if cache is older than 1 minute
    
    if ranking_data is None:
        today = timezone.now().date()

        if type == 'alltime':
            # Calculate all-time ranking based on all votes
            ranking_data = Books.objects.annotate(score=models.Count('vote')).order_by('-score')

        elif type == 'annual':
            # Calculate annual ranking based on votes within the current year
            ranking_data = Books.objects.filter(vote__vote_date__year=today.year).annotate(score=models.Count('vote')).order_by('-score')

        elif type == 'monthly':
            # Calculate monthly ranking based on votes within the current month
            ranking_data = Books.objects.filter(vote__vote_date__year=today.year, vote__vote_date__month=today.month).annotate(score=models.Count('vote')).order_by('-score')

        elif type == 'weekly':
            # Calculate weekly ranking based on votes within the current week
            start_of_week = today - timezone.timedelta(days=today.weekday())
            ranking_data = Books.objects.filter(vote__vote_date__gte=start_of_week).annotate(score=models.Count('vote')).order_by('-score')

        elif type == 'daily':
            # Calculate daily ranking based on votes within the current day
            ranking_data = Books.objects.filter(vote__vote_date=today).annotate(score=models.Count('vote')).order_by('-score')

        # Store the calculated ranking in the cache
        cache.set(cache_key, ranking_data)
        
        # Update the cache timestamp
        cache.set(cache_timestamp_key, timezone.now())
    if ranking_data.count() < 10:
        remaining_books = Books.objects.exclude(pk__in=ranking_data.values_list('pk', flat=True))[:10 - ranking_data.count()] 
        ranking_data = list(chain(ranking_data, remaining_books))
    # for book in ranking_data:
    #     print (f"{book.Title} - {book.score}")
    context = {
        'books': ranking_data,
        'type':type
    }
    return render(request, 'books/ranking.html', context)

def create_folder(request):
    if request.method == 'POST':
        folder_name = request.POST.get('folderName')
        user_library = UserLibrary.objects.get(user=request.user)

        try:
            # Check if a folder with the same name already exists in the user's library
            existing_folder = Folder.objects.get(name=folder_name, user_library=user_library)
            return JsonResponse({'success': False, 'error': 'Folder with the same name already exists.'})
        except ObjectDoesNotExist:
            # Create a new folder if it doesn't already exist
            folder = Folder.objects.create(name=folder_name, user_library=user_library)
            return JsonResponse({'success': True, 'folder_id': folder.id})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def assign_to_folder(request):
    book_id = request.POST.get('bookId')
    folder_name = request.POST.get('folderName')

    try:
        book = Books.objects.get(pk=book_id)
        lib=UserLibrary.objects.get(user=request.user)
        user_book = UserBook.objects.filter(folder__user_library=lib,book=book).first()
        if user_book:
            user_book.delete()
        if folder_name!='none':
            folder = Folder.objects.get(name=folder_name, user_library=lib)
            UserBook.objects.create(book=book, folder=folder)

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def delete_folder(request):
    folder_name = request.POST.get('folderName')
    user_library=UserLibrary.objects.get(user=request.user)
    try:
        folder = Folder.objects.get(name=folder_name,user_library=user_library)
        folder.delete()
        return JsonResponse({'success': True})
    except Folder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Folder not found.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
def writer_desk(request):
    context={}
    usr=request.user.userprofile
    if not usr.is_author:
        return render(request,'books/write.html',{'false':True})
    author=Authors.objects.get(AuthorName=request.user.username,Biography=request.user.userprofile.bio)
    books=Books.objects.filter(Author=author)
    book_chapters = {
        book.BookID: Chapter.objects.filter(book=book)
        for book in books
    }
    categories=Category.objects.all()
    languages = Languages.objects.all()
    context['categories']=categories
    context['languages']=languages
    context['books']=books
    context['social_media_links']=author.social_media_links.all()
    context['book_chapters']=book_chapters
    return render(request,'books/write.html',context)

@login_required
def writer_yes(request):
    usr = request.user.userprofile
    if not usr.is_filled():
        messages.error(request, "Please fill out all fields in your profile before proceeding")
        return redirect('user_profile')
    if not usr.is_author:
        author = Authors.objects.create(
            AuthorName=usr.user.username,
            Biography=usr.bio,
            profile_image=usr.profile_image if usr.profile_image else None
            )
        author.save() 
        usr.is_author = True
        usr.save()
    return redirect('writer_desk')

@login_required
def writer_no(request):
    return redirect('/')

@login_required
def new_book(request):
    if request.method == "POST":
        # Extract data from the form submission
        title = request.POST.get('title')
        description = request.POST.get('description')
        language_id = request.POST.get('language')
        cover_image = request.FILES.get('cover_image')
        categories = request.POST.getlist('categories')
        cats=Category.objects.filter(id__in=categories)
        author=Authors.objects.get(AuthorName=request.user.username,Biography=request.user.userprofile.bio)
        if cover_image is None:
            # Set default image path
            default_image_path = 'book/book_cover/noimage.jpg'  # Adjust the default image path as needed
            # Assign the default image path to cover_image
            cover_image = default_image_path
        # Create a new Books object
        new_book = Books.objects.create(
            Title=title,
            Description=description,
            LanguageID_id=language_id,
            cover_image=cover_image,
            Author=author,
            isOriginal=True,
            PublicationYear=datetime.now().year
        )
        # Add categories to the book
        new_book.Categories.add(*categories)
        # Redirect to writer_desk after creating the book
        return redirect('writer_desk')

@login_required
def set_socials(request):
    if request.method=="POST" and request.POST.getlist('social_media_links'):
        author=Authors.objects.get(AuthorName=request.user.username,Biography=request.user.userprofile.bio)
        author.social_media_links.clear()
        links=request.POST.getlist('social_media_links')
        print(request.POST)
        for url in links:
        # Extract the domain from the URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Determine the platform based on the domain
            if 'twitter' in domain:
                platform = 'twitter'
            elif 'facebook' in domain:
                platform = 'facebook'
            elif 'instagram' in domain:
                platform = 'instagram'
            else:
                platform = 'other'
            
            # Get or create the SocialMediaLink instance
            social_media_link, created = SocialMediaLink.objects.get_or_create(
                platform=platform,
                link=url
            )
            if social_media_link:
                author.social_media_links.add(social_media_link)
            elif created:
                 author.social_media_links.add(social_media_link)
    if request.method=="POST" and not request.POST.getlist('social_media_links'):
        author=Authors.objects.get(AuthorName=request.user.username,Biography=request.user.userprofile.bio)
        author.social_media_links.clear()
    return redirect('writer_desk')

def update_book(request):
    if request.method == 'POST':
        # Extract form data
        book_id = request.POST.get('book_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        cover_image = request.FILES.get('cover_image')
        price = request.POST.get('price')

        # Update book object
        book = Books.objects.get(BookID=book_id)
        book.Title = title
        book.Description = description
        if cover_image:
            book.cover_image = cover_image
        book.Price=price
        book.save()

        # Redirect to the appropriate page (e.g., book details page)
        return redirect('writer_desk')

def chap_upload(request):
    if request.method == 'POST':
        # Retrieve data from the form
        book_id = request.POST.get('book_id')  # Assuming you have a hidden input field for book_id
        chapter_number = request.POST.get('chapter_number')
        chapter_title = request.POST.get('title')
        chapter_contents = request.POST.get('editor')
        chapter, created = Chapter.objects.get_or_create(book_id=book_id, chapter_number=chapter_number)
        chapter.chapter_title = chapter_title
        chapter.chapter_contents = chapter_contents
        chapter.save()
    return redirect('writer_desk')

def fetch_chapter(request, book_id, chapter_number):
    try:
        chapter = Chapter.objects.get(book_id=book_id, chapter_number=chapter_number)
        data = {
            'title': chapter.chapter_title,
            'content': chapter.chapter_contents
        }
        print(chapter.chapter_title)
        return JsonResponse(data)
    except Chapter.DoesNotExist:
        return JsonResponse({'error': 'Chapter not found'}, status=404)
    
def original_chap(request,book_id,chapter_num):
    
    lib=UserLibrary.objects.filter(user=request.user).first()
    book = get_object_or_404(Books, BookID=book_id)
    if book not in lib.books.all() and chapter_num>8:
        raise Http404
    user_cart = ShoppingCart.objects.filter(user=request.user).first()
    if user_cart:
        cart_item_count = user_cart.items.count()
    else:
        cart_item_count = 0
    if book.isOriginal:
        chapter=Chapter.objects.get(book=book,chapter_number=chapter_num)
        prev_chapter_url = None
        next_chapter_url = None
        if chapter_num > 1:
            prev_chapter_url = reverse('original_chap', args=[book_id, chapter_num - 1])

        total_chapters = Chapter.objects.filter(book=book).count()
        if chapter_num < total_chapters:
            next_chapter_url = reverse('original_chap', args=[book_id, chapter_num + 1])
    else:
        raise Http404
    context = {
                    'chapter_content': chapter.chapter_contents,
                    'book':book,
                    'cart_item_count':cart_item_count,
                    'prev_chapter':prev_chapter_url,
                    'next_chapter':next_chapter_url

                }
    return render(request,'books/read.html',context)

@require_POST
def delete_book(request):
    book_id = request.POST.get('book_id')
    try:
        book = Books.objects.get(BookID=book_id, isOriginal=True) 
        book.delete()
        return JsonResponse({'message': 'Book deleted successfully.'})
    except Books.DoesNotExist:
        return JsonResponse({'error': 'Book not found or not original.'}, status=400)
    
def forum(request):
    if request.method == 'POST':
        title = request.POST.get('post_title')
        content = request.POST.get('post_content')
        book_id = request.POST.get('post_book')
        # Assuming the current user is the author of the post
        author = request.user
        print(request.POST)
        if title and content and book_id:
            try:
                book_id = int(book_id)
                book = Books.objects.get(pk=book_id)
                post = Post.objects.create(title=title, content=content, book=book, author=author)
                return redirect('forum')  # Redirect to the forum home page
            except (ValueError, Books.DoesNotExist):
                pass  # Handle invalid book ID
    context={}
    books=Books.objects.all()
    o_posts=Post.objects.filter(book__isOriginal=True)
    p_posts=Post.objects.filter(book__isOriginal=False)
    context['books']=books
    context['p_posts']=p_posts
    context['o_posts']=o_posts
    return render(request,'books/forum.html',context)

def view_post(request, post_id):
    context = {}
    post = Post.objects.get(pk=post_id)
    context['post'] = post
    
    # Get or create ViewPost instance
    view_post, created = ViewPost.objects.get_or_create(user=request.user, post=post)
    if created:
        post.calculate_count()

    # Check if the post is liked by the user
    try:
        liked_post = LikePost.objects.get(user=request.user, post=post)
        context['liked'] = True
    except LikePost.DoesNotExist:
        context['liked'] = False    

    # Get replies associated with the post
    replies = Reply.objects.filter(post=post)
    context['replies'] = replies
    profile_image_urls = {}

    for reply in replies:
        user=reply.user
        user_profile = UserProfile.objects.get(user=user)
        profile_image_urls[user.username] = user_profile.profile_image.url if user_profile.profile_image else None
    context['profile_image_urls']=profile_image_urls
    return render(request, 'books/post_details.html', context)

def like_post(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        user = request.user
        
        # Check if LikePost object already exists
        try:
            like_post = LikePost.objects.get(post_id=post_id, user=user)
            like_post.delete()  # If exists, delete it
        except LikePost.DoesNotExist:
            LikePost.objects.create(post_id=post_id, user=user)  # If not exists, create it
        
        # Recalculate LikePosts count for the post
        post = Post.objects.get(pk=post_id)
        post.likes = LikePost.objects.filter(post=post).count()
        post.save()

        return JsonResponse({'success': True,'like_count':post.likes})
    else:
        return JsonResponse({'success': False})
    
def submit_reply(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        reply_content = request.POST.get('reply_content')
        if reply_content:
            Reply.objects.create(post=post, user=request.user, content=reply_content)
            # You may want to add additional logic here, such as updating the last activity of the post
            return redirect('view_post', post_id=post_id)  # Redirect to the post detail page