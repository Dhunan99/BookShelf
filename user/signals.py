from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
from books.models import UserLibrary,Books

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

@receiver(post_save, sender=User)
def create_user_library(sender, instance, created, **kwargs):
    if created:
        # Create a UserLibrary instance for the new user
        UserLibrary.objects.create(user=instance)

@receiver(post_save, sender=Books)
@receiver(post_delete, sender=Books)
def update_author_book_count(sender, instance, **kwargs):
    author = instance.Author
    author.calculate_number_of_works()

from django.db.models.signals import pre_save
from django.dispatch import receiver

@receiver(pre_save, sender=Books)
def set_default_price(sender, instance, **kwargs):
    if instance.Price is None:
        instance.Price = 1