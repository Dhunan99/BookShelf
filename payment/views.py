from django.shortcuts import render,redirect
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from .models import Order
from books.models import Books
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from books.views import add_to_library,UserLibrary
from user.models import ShoppingCart,PurchaseHistory
from datetime import datetime
from django.template.loader import render_to_string
from django.utils import timezone
import os
from django.core.mail import EmailMessage
from xhtml2pdf import pisa
from django.db.models import F
from django.views.decorators.cache import cache_control

# authorize razorpay client with API Keys.
razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
 
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@login_required
def homepage(request, book_id):
    currency = 'INR'

    try:
        # Retrieve the book with the matching book_id
        book = Books.objects.get(pk=book_id)

        # Check if the book is already in the user's library
        user_library = UserLibrary.objects.get_or_create(user=request.user)
        if book in user_library[0].books.all():
            return HttpResponseBadRequest("Book is already in your library")

        # Get the price of the book as a Decimal
        amount = Decimal(book.Price)  # Convert to Decimal

        # Convert the Decimal amount to a float for Razorpay
        amount_in_paise = float(amount * 100)  # Convert to paise (assuming price is in rupees)

        # Create a Razorpay Order
        razorpay_order = razorpay_client.order.create(dict(amount=amount_in_paise,
                                                           currency=currency,
                                                           payment_capture='0'))

        # Order ID of the newly created order.
        razorpay_order_id = razorpay_order['id']
        callback_url = "http://" + "127.0.0.1:8000" + "/paymenthandler/pay/"

        # Create an Order instance with status set as "pending" and associate the book
        order = Order.objects.create(
            user=request.user,
            razorpay_order_id=razorpay_order_id,
            payment_id="",
            amount=amount,  # Store as Decimal
            currency=currency,
            payment_status=Order.PaymentStatusChoices.PENDING,  # Set as "Pending"
        )

        # Add the book to the items field of the order
        order.items.add(book)

        # Pass order details to the frontend
        context = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_merchant_key': settings.RAZOR_KEY_ID,
            'razorpay_amount': amount_in_paise,  # Use the float amount for Razorpay
            'currency': currency,
            'callback_url': callback_url,
            'amount': amount_in_paise/100,
            'title': "'" + book.Title + "'"
        }

        return render(request, 'payment/index.html', context=context)
    except Books.DoesNotExist:
        # Handle the case where the book with the given ID doesn't exist
        return HttpResponseBadRequest("Book not found")
 
 
# we need to csrf_exempt this url as
# POST request will be made by Razorpay
# and it won't have the csrf token.
@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        # Verify the payment signature.
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        result = razorpay_client.utility.verify_payment_signature(
            params_dict)
        if result is False:
            # Signature verification failed.
            return render(request, 'payment/paymentfail.html')
        else:
            # Signature verification succeeded.
            # Retrieve the order from the database
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)

            # Check if all the books in the order are in the user's cart
            try:
                user_cart = ShoppingCart.objects.get(user=request.user)
            except ShoppingCart.DoesNotExist:
                user_cart = ShoppingCart.objects.create(user=request.user)

            book_ids = order.items.values_list('BookID', flat=True)

            if len(book_ids) >1:
                # All books are in the cart, call a different function
                for book_id in book_ids:
                    add_to_library(request.user, book_id,alt=True)
                total_price = sum(book.Price for book in user_cart.items.all())
                purchase_history = PurchaseHistory.objects.create(
                    user=user_cart.user,
                    total_price=total_price,
                    purchase_date=datetime.now(),
                    order=order
                )
                purchase_history.items.set(user_cart.items.all())
                user_cart.items.clear()
                user_cart.update_total_price()
            else:
                # Not all books are in the cart, add them to the library
                for book_id in book_ids:
                    add_to_library(request.user, book_id,order1=order)
                user_cart.update_total_price()
                purchase_history = PurchaseHistory.objects.filter(user=request.user).order_by(F('purchase_date').desc(nulls_last=True)).first()
            user_cart.save()
            # Capture the payment with the amount from the order
            amount = int(order.amount * 100)  # Convert Decimal to paise
            razorpay_client.payment.capture(payment_id, amount)

            # Update the order with payment ID and change status to "Successful"
            order.payment_id = payment_id
            order.payment_status = Order.PaymentStatusChoices.SUCCESSFUL
            order.save()
            l=[purchase_history]
            context = {
            'purchase_history': l,
            'start_date': datetime.now(),
            'total_price': order.amount,
        }
        receipt_html = render_to_string('user/receipt.html', context)

        # Create a PDF file
        pdf_file_path = os.path.join(settings.MEDIA_ROOT, 'receipt.pdf')
        with open(pdf_file_path, 'w+b') as pdf_file:
            pisa.pisaDocument(receipt_html.encode("UTF-8"), pdf_file)

        # Send an email with the PDF receipt as an attachment
        subject = '📚 Your BookShelf Purchase Receipt'
        print(order,purchase_history)
# Customize the message
        message = f"""
    Hello there bookworm! 📖

    We hope you're as excited as we are about your recent book purchase. 🤩

    Your purchase details are here to make your day even better:

    📅 Date & Time: { purchase_history.purchase_date.strftime("%Y-%m-%d %H:%M:%S") }
    💼 Order Number: { order.razorpay_order_id }
    📚 Book(s) Purchased: { ', '.join([item.Title for item in purchase_history.items.all()]) }
    💰 Total Amount: Rs. { order.amount }

    Thank you for choosing our bookstore. Happy reading! 📖✨

    Warm regards,
    BookShelf Team
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [request.user.email]

        email = EmailMessage(subject, message, from_email, recipient_list)
        email.attach_file(pdf_file_path, 'application/pdf')
        email.send()

        # Clean up: Remove the temporary PDF file
        os.remove(pdf_file_path)
            # Redirect to a success page or return a success response
        return redirect('/books/user_library/')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)   
@login_required
def checkout(request):
    currency = 'INR'

    try:
        # Retrieve the user's shopping cart items
        cart = ShoppingCart.objects.get(user=request.user)
        cart_items = cart.items.all()

        # Calculate the total price of cart items
        total_price = sum(book.Price for book in cart_items)
        
        # Convert the total_price to a float
        amount = float(total_price)

        # Convert the float amount to paise (assuming price is in rupees)
        amount_in_paise = int(amount * 100)

        # Create a Razorpay Order
        razorpay_order = razorpay_client.order.create(dict(amount=amount_in_paise, currency=currency, payment_capture='0'))
        razorpay_order_id = razorpay_order['id']
        callback_url = "http://" + "127.0.0.1:8000" + "/paymenthandler/pay/"

        # Create an Order instance with status set as "pending" and associate cart items
        order = Order.objects.create(
            user=request.user,
            razorpay_order_id=razorpay_order_id,
            payment_id="",
            amount=Decimal(amount),  # Store as Decimal
            currency=currency,
            payment_status=Order.PaymentStatusChoices.PENDING
        )
        order.items.set(cart_items)
        # Pass order details to the frontend
        context = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_merchant_key': settings.RAZOR_KEY_ID,
            'razorpay_amount': amount_in_paise,
            'currency': currency,
            'callback_url': callback_url,
            'amount': amount_in_paise / 100,
            'books': cart_items,
        }

        return render(request, 'payment/index.html', context=context)

    except ShoppingCart.DoesNotExist:
        return HttpResponseBadRequest("Shopping cart not found")