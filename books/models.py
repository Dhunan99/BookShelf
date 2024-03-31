# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import os
from user.models import NotificationType,Notification
from django.contrib.contenttypes.models import ContentType
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment import SentimentIntensityAnalyzer
from django.db.models import Avg, F,Value,FloatField,Q
from django.db.models.functions import Coalesce
class SocialMediaLink(models.Model):
    PLATFORM_CHOICES = (
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        # Add more social media platforms as needed
    )
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    link = models.URLField()
    
    def __str__(self):
        return f"{self.platform}: {self.link}"
    
class Authors(models.Model):
    Author = models.AutoField(primary_key=True)
    AuthorName = models.CharField(max_length=100)
    Biography = models.TextField(blank=True, null=True)
    social_media_links = models.ManyToManyField(SocialMediaLink, blank=True)
    number_of_works = models.PositiveIntegerField(default=0)
    profile_image = models.ImageField(upload_to='authors/', blank=True, null=True)
    class Meta:
        verbose_name_plural = "Authors"
    def __str__(self):
        return self.AuthorName
    def calculate_number_of_works(self):
        # Calculate the number of works for the author and update the field
        self.number_of_works = self.books_set.count()
        self.save()
    def sync_with_user_profile(self, user_profile):
        """
        Update Author model with UserProfile data
        """
        # Assuming user_profile is an instance of UserProfile
        self.AuthorName=user_profile.user.username
        self.Biography = user_profile.bio
        self.profile_image = user_profile.profile_image
        self.save()

class Languages(models.Model):
    LanguageID = models.AutoField(primary_key=True)
    LanguageName = models.CharField(max_length=50)
    class Meta:
        verbose_name_plural = "Languages"
    def __str__(self):
        return self.LanguageName

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Categories"

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Tags"

class Identifier(models.Model):
    IDENTIFIER_CHOICES = (
        ('ASIN', 'ASIN'),
        ('ISBN', 'ISBN'),
    )

    identifier_type = models.CharField(max_length=4, choices=IDENTIFIER_CHOICES)

def validate_pdf_file(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Only PDF files are allowed.')
    
class Books(models.Model):
    BookID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=200)
    Author = models.ForeignKey(Authors, on_delete=models.CASCADE)
    PublicationYear = models.PositiveIntegerField()
    Categories = models.ManyToManyField(Category)
    Description = models.TextField()
    LanguageID = models.ForeignKey(Languages, on_delete=models.CASCADE)
    Price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cover_image = models.ImageField(upload_to='book/book_cover')
    tags = models.ManyToManyField(Tag, blank=True, null=True)
    IDENTIFIER_CHOICES = (
        ('ASIN', 'ASIN'),
        ('ISBN', 'ISBN'),
    )
    identifier_type = models.CharField(max_length=4, choices=IDENTIFIER_CHOICES, blank=True, null=True)
    identifier_value = models.CharField(max_length=20, blank=True, null=True) 
    epub_file = models.FileField(upload_to='book/epubs/', blank=True, null=True)
    isOriginal = models.BooleanField(default=False)
    rating = models.FloatField(null=True, blank=True)
    rating_count = models.PositiveIntegerField(default=0)
    class Meta:
        verbose_name_plural = "Books"
    def __str__(self):
        return self.Title
    def calculate_average_rating(self):
        # Calculate the average rating and update the rating and rating_count fields
        reviews = Review.objects.filter(book=self)
        if reviews.exists():
            total_rating = sum([review.overall_rating for review in reviews])
            self.rating = total_rating / reviews.count()
            self.rating_count = reviews.count()
        else:
            self.rating = None
            self.rating_count = 0
        self.save()
    @classmethod
    def assign_tags(cls):
        # Calculate comprehensive score and order by it
        annotated_books = cls.objects.annotate(
            comprehensive_score=Coalesce(
                Avg(F('rating')) * 0.3 +
                Avg(F('rating_count')) * 0.1 +
                Avg(F('review__sentiment_score')) * 0.6,
                Value(0.0, output_field=FloatField())
            )
        ).order_by('-comprehensive_score')

        # Get the 'popular' tag
        popular_tag, created = Tag.objects.get_or_create(name='Popular')
        for book in cls.objects.filter(tags=popular_tag):
            book.tags.remove(popular_tag)
        # Assign the 'popular' tag to the top 3 books
        top_books = annotated_books[:3]
        for book in top_books:
            book.tags.add(popular_tag)
    

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    review = models.TextField()
    style_rating = models.PositiveIntegerField(null=False, blank=True)
    story_rating = models.PositiveIntegerField(null=False, blank=True)
    grammar_rating = models.PositiveIntegerField(null=False, blank=True)
    character_rating = models.PositiveIntegerField(null=False, blank=True)
    overall_rating = models.FloatField(null=False, blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    likes_count = models.PositiveIntegerField(default=0)
    sentiment_score = models.FloatField(null=True)
    class Meta:
        # Add a unique constraint to ensure one review per user per book
        unique_together = ('user', 'book')

    def __str__(self):

        return f"Review from '{self.user.username}' for '{self.book.Title}' by '{self.book.Author}'"
    def update_likes_count(self):
        # Calculate the likes_count based on the number of likes for this review
        self.likes_count = self.like_set.count()
        self.save()

    def delete(self, *args, **kwargs):
        # Delete the review instance
        super(Review, self).delete(*args, **kwargs)
        self.book.calculate_average_rating()
        
    def calculate_sentiment_score(self):
        sia = SentimentIntensityAnalyzer()
        combined_text = f"{self.review} Overall Rating: {self.overall_rating}"
        sentiment_score = sia.polarity_scores(combined_text)['compound']
        self.sentiment_score = sentiment_score
        self.save()

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'review')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Check if the review's author is different from the user who liked it
        if self.user != self.review.user:
            # Create a notification for the review author
            Notification.objects.create(
                sender=self.user,   
                recipient=self.review.user,
                notification_type=NotificationType.LIKE,  # Set the notification type to LIKE
                content_type=ContentType.objects.get_for_model(self),  # Set the content_type
                object_id=self.id,  # Set the object_id to the Like instance's id
                extra_content=self.review.book.Title
            )

class UserLibrary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    books = models.ManyToManyField(Books, blank=True)

    def __str__(self):
        return f"Library of {self.user.username}"
    class Meta:
        verbose_name_plural = "User Libraries"

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    dismissed = models.BooleanField(default=False)
    def __str__(self):
        return f"Report by '{self.user.username}' on '{self.review}'"

    class Meta:
        unique_together = ('user', 'review')

class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    vote_date = models.DateField()  # Date of the vote


    def __str__(self):
        return f"Vote by {self.user.username} for {self.book.Title} on {self.vote_date}"
    @classmethod
    def has_user_voted_today(cls, user):
        today = timezone.now().date()
        return cls.objects.filter(user=user, vote_date=today).exists()

class Folder(models.Model):
    name = models.CharField(max_length=255)
    user_library = models.ForeignKey('UserLibrary', on_delete=models.CASCADE, related_name='folders')

    def __str__(self):
        return f"{self.name} (User: {self.user_library.user.username})"
    
class UserBook(models.Model):
    book = models.ForeignKey('Books', on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('folder', 'book')  # Enforce unique combination of user library and book

    def __str__(self):
        return f"User: {self.folder.user_library}, Book: {self.book.Title}, Folder: {self.folder.name}"

class Chapter(models.Model):
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    chapter_number = models.PositiveIntegerField()
    chapter_title = models.CharField(max_length=200)
    chapter_contents = models.TextField()

    class Meta:
        unique_together = ('book', 'chapter_number')  # Ensure uniqueness of chapter number within each book

    def __str__(self):
        return f"{self.book.Title} - Chapter {self.chapter_number}: {self.chapter_title}"
    
class Post(models.Model):
    book = models.ForeignKey(Books, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    likes = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    replies = models.PositiveIntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    def calculate_count(self):
        self.views = self.viewpost_set.count()
        self.save()
    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save()
    
class LikePost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')
        
    def save(self, *args, **kwargs):
        self.post.update_last_activity()
        super().save(*args, **kwargs)

class ViewPost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')
    
    def save(self, *args, **kwargs):
        self.post.update_last_activity()
        super().save(*args, **kwargs)
        
class Reply(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.post.update_last_activity()
        super().save(*args, **kwargs)

class Contact(models.Model):
    reason = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    addressed = models.BooleanField(default=False)  # New field

    def __str__(self):
        return f"{self.reason} - {self.created_at}"