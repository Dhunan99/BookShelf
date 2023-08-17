from django.shortcuts import render, redirect,get_object_or_404
from .forms import BookForm
from .models import Authors, Languages, Books
from django.contrib.auth.decorators import user_passes_test
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
                AuthorID=author,
                ISBN=form.cleaned_data['isbn'],
                PublicationDate=form.cleaned_data['publication_date'],
                Category=form.cleaned_data['category'],
                Description=form.cleaned_data['description'],
                LanguageID=language,
                Price=form.cleaned_data['price'],
                cover_image = form.cleaned_data['cover_image']
            )
            return render(request,'books/book_added.html')  # Redirect to a success page

    else:
        form = BookForm()
    return render(request, 'books/add_book.html', {'form': form})

def book_list(request):
    books = Books.objects.all()
    return render(request, 'books/book_list.html', {'books': books})

@user_passes_test(user_is_superuser)
def delete_book(request, book_id):
    book = get_object_or_404(Books, pk=book_id)
    if request.method == 'POST':
        book.delete()
        return redirect('/books/book_list')  # Redirect to your books list page
    return render(request, 'books/delete_book.html', {'book': book})