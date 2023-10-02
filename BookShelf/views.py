from django.shortcuts import redirect,render
from user.models import OTPModel, UserProfile
from books.models import SocialMediaLink, Authors, Languages, Category, Tag, Identifier, Books, Review, Like, UserLibrary
from django.contrib.auth.decorators import user_passes_test
def redir(request):
    if request.user.is_authenticated:
        return redirect('/user/home')
    return redirect('/user/login')


def user_is_superuser(user):
    return user.is_superuser

@user_passes_test(user_is_superuser)
def stats(request):
    user_profile_data = UserProfile.objects.all()
    social_media_links = SocialMediaLink.objects.all()
    authors_data = Authors.objects.all()
    languages_data = Languages.objects.all()
    categories_data = Category.objects.all()
    tags_data = Tag.objects.all()
    books_data = Books.objects.all()
    reviews_data = Review.objects.all()
    likes_data = Like.objects.all()

    # Pass the data to the template
    context = {
        'user_count': len(user_profile_data),
        'social_links': len(social_media_links),
        'author_count': len(authors_data),
        'language_count': len(languages_data),
        'category_count': len(categories_data),
        'tag_count': len(tags_data),
        'book_count': len(books_data),
        'review_count': len(reviews_data),
        'like_count': len(likes_data),
    }
    return render(request,'stats.html',context)