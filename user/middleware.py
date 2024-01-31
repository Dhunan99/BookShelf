# middleware.py
from django.utils import timezone
from .models import UserActivity

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_activity, created = UserActivity.objects.update_or_create(
                user=request.user,
                defaults={'last_activity': timezone.now()},
            )
        response = self.get_response(request)
        return response
