from django.contrib import admin
from .models import Order
# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'razorpay_order_id', 'payment_id', 'amount', 'currency', 'payment_status', 'timestamp')
    list_filter = ('user', 'payment_status', 'timestamp')
    search_fields = ('user__username', 'razorpay_order_id', 'payment_id')
    list_editable = ('payment_status',)
    list_per_page = 20

admin.site.register(Order, OrderAdmin)
