from django.shortcuts import redirect,render
from django.contrib.auth.models import User
from user.models import OTPModel, UserProfile
from books.models import SocialMediaLink, Authors, Languages, Category, Tag, Books, Review, Like,Report
from payment.models import Order
from django.db.models import Sum
from django.contrib.auth.decorators import user_passes_test
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, fields
from django.utils import timezone
from datetime import date
from books.models import Contact
from django.views.decorators.http import require_POST
from django.http import JsonResponse

def redir(request):
    if request.user.is_authenticated:
        return redirect('/user/home')
    return redirect('/user/login')


def user_is_superuser(user):
    return user.is_superuser

@user_passes_test(user_is_superuser)
def stats(request):
    user_profile_data = UserProfile.objects.all().count()
    social_media_links = SocialMediaLink.objects.all().count()
    authors_data = Authors.objects.all().count()
    languages_data = Languages.objects.all().count()
    categories_data = Category.objects.all().count()
    tags_data = Tag.objects.all().count()
    books_data = Books.objects.all().count()
    reviews_data = Review.objects.all().count()
    likes_data = Like.objects.all().count()
    reports_data=Report.objects.all().count()
    order_data=Order.objects.all().count()
    total_amount = Order.objects.aggregate(total_amount=Sum('amount'))['total_amount']
    dismissed_reports=Report.objects.filter(dismissed=True).count()
    pending_reports=reports_data-dismissed_reports
    successful_orders = Order.objects.filter(payment_status='successful').count()
    pending_orders=order_data-successful_orders
    books_with_rating = Books.objects.filter(review__isnull=False).count()
    one_week_ago = timezone.now() - timedelta(days=7)
    active_users = User.objects.filter(last_login__gte=one_week_ago).count()
    male_users = User.objects.filter(userprofile__gender='M').count()
    female_users = User.objects.filter(userprofile__gender='F').count()
    other_users = User.objects.filter(userprofile__gender='O').count()
    undisclosed=user_profile_data-male_users-female_users-other_users
    users_with_age = UserProfile.objects.annotate(
        age=ExpressionWrapper(
            F('dob'),
            output_field=fields.DateField()
        )
    )
    today = date.today()
    # Calculate the average age
    total_age = sum((today - user.age).days // 365 for user in users_with_age if user.age is not None)
    user_count = users_with_age.filter(age__isnull=False).count()
    average_age = total_age / user_count if user_count > 0 else 0
    # Pass the data to the template
    context = {
        'user_count': user_profile_data,
        'social_links': social_media_links,
        'author_count': authors_data,
        'language_count': languages_data,
        'category_count': categories_data,
        'tag_count': tags_data,
        'book_count': books_data,
        'review_count': reviews_data,
        'like_count': likes_data,
        'order_count':order_data,
        'report_count':reports_data,    
        'dismissed_reports':dismissed_reports,
        'pending_reports':pending_reports,
        'successful_orders':successful_orders,
        'pending_orders':pending_orders,
        'total_amount':total_amount,
        'books_with_rating':books_with_rating,
        'active_users':active_users,
        'male_users':male_users,
        'female_users':female_users,
        'other_users':other_users,
        'undisclosed':undisclosed,
        'average_age':average_age
    }
    return render(request,'stats.html',context)

def contact(request):
    if request.method == 'POST':
        reason = request.POST.get('reason')
        message = request.POST.get('message')
        Contact.objects.create(reason=reason, message=message,user=request.user)
        return render(request,'contact.html',{'success':True})
    return render(request,'contact.html')

@user_passes_test(user_is_superuser)
def contacts(request):
    contacts=Contact.objects.filter(addressed=False)
    return render(request,'contacts.html',{'contacts':contacts})

@require_POST
def address_contact(request):
    contact_id = request.POST.get('contact_id')
    try:
        contact = Contact.objects.get(id=contact_id)
        contact.addressed = True
        contact.save()
        return JsonResponse({'success': True})
    except Contact.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Contact not found'})

@require_POST
def invalidate_contact(request):
    contact_id = request.POST.get('contact_id')
    try:
        contact = Contact.objects.get(id=contact_id)
        contact.delete()
        return JsonResponse({'success': True})
    except Contact.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Contact not found'})