from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from ckeditor.fields import RichTextField

# class Member(models.Model):
#     UserName=models.CharField(max_length=26)
#     Email=models.EmailField()
#     profile_pic=models.ImageField(upload_to='dp',blank=True)
#     def __str__(self):
#         return self.UserName
class OTPModel(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return self.expires_at > timezone.now()
    
    def __str__(self):
        return f"OTP for {self.user.username}"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_author = models.BooleanField(default=False)
    bio = models.TextField(blank=True)
    gender = models.CharField(max_length=20, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True)
    dob = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(upload_to='user/profile_images/', blank=True, null=True)

    def __str__(self):
        return self.user.username
    

class ShoppingCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shopping_carts')
    items = models.ManyToManyField('books.Books', blank=True, related_name='carts')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Shopping cart for {self.user.username}"
    
    def update_total_price(self):
        # Calculate the total price of the items in the cart
        total_price = sum(book.Price for book in self.items.all())
        
        # Update the total_price field with the calculated value
        self.total_price = total_price
        self.save()
        

class PurchaseHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchase_histories')
    items = models.ManyToManyField('books.Books', related_name='purchases')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField()
    order = models.OneToOneField('payment.Order', on_delete=models.SET_NULL, null=True, related_name='purchase_history')


    def __str__(self):
        return f"Purchase history for {self.user.username} - {self.purchase_date}"
    class Meta:
        verbose_name_plural="Purchase Histories"

class NotificationType(models.TextChoices):
    LIKE = 'like', 'Like'
    MESSAGE = 'message', 'Message'
    FRIEND_REQUEST = 'friend_request', 'Friend Request'
    # Add more notification types as needed

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    extra_content=models.CharField(max_length=50, blank=True,null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return f'{self.sender} to {self.recipient}: {self.get_notification_type_display()}'

    def mark_as_read(self):
        self.is_read = True
        self.save()

    @property
    def notification_message(self):
        if self.notification_type == NotificationType.LIKE:
            return f"{self.sender} liked your review for '{self.extra_content}'"
        elif self.notification_type == NotificationType.MESSAGE:
            return f'You have a new message from {self.sender}.'
        elif self.notification_type == NotificationType.FRIEND_REQUEST:
            return f'{self.sender} sent you a friend request.'
        # Add more notification messages as needed
class UserActivity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_activity = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.user} was last active at {self.last_activity}'
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    read_status=models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} to {self.receiver}: {self.content}"
    
    def create_notification(self):
        if not Notification.objects.filter(
            recipient=self.receiver,
            sender=self.sender,
            notification_type=NotificationType.MESSAGE,
            is_read=False,
        ).exists():
            # Create a new notification
            Notification.objects.create(
                sender=self.sender,
                recipient=self.receiver,
                notification_type=NotificationType.MESSAGE,
                content_type=ContentType.objects.get_for_model(self),
                object_id=self.id)
    
class ReadingProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey('books.Books', on_delete=models.CASCADE)
    current_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.book.Title} - {self.current_url}"
    
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.URLField()  # Save the URL associated with the comment
    content = RichTextField()
    created_at = models.DateTimeField(auto_now_add=True)