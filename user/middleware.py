# middleware.py
from django.utils import timezone
from .models import UserActivity

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            current_time = timezone.now()

            # Check if the last update was more than 5 minutes ago
            last_update_threshold = current_time - timezone.timedelta(minutes=1)
            user_activity, created = UserActivity.objects.get_or_create(
                user=request.user,
                defaults={'last_activity': current_time},
            )

            # Update the last activity only if it's been more than 5 minutes
            if user_activity.last_activity < last_update_threshold:
                user_activity.last_activity = current_time
                user_activity.save()

        response = self.get_response(request)
        return response
