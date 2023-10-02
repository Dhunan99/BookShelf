from django.db import models
from django.contrib.auth.models import User
from books.models import Books
from django.utils import timezone
# Create your models here.
class Order(models.Model):
    class PaymentStatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESSFUL = 'successful', 'Successful'
        FAILED = 'failed', 'Failed'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=255)
    payment_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3)
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.PENDING)
    timestamp = models.DateTimeField(auto_now_add=True)
    items = models.ManyToManyField(Books)  # Use the correct model name 'Book'

    def __str__(self):
        return f"Order for {self.user.username}"

    class Meta:
        ordering = ['-timestamp']

#Update Status not implemented
    def update_status(self):
        # Calculate the time difference in minutes
        time_difference = (timezone.now() - self.timestamp).total_seconds() / 60

        if self.payment_status == self.PaymentStatusChoices.PENDING and time_difference > 1:
            # Update the status to "Failed"
            self.payment_status = self.PaymentStatusChoices.FAILED
            self.save()