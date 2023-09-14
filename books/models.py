# Create your models here.
from django.db import models
from django.contrib.auth.models import User

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

class Books(models.Model):
    BookID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=200)
    Author = models.ForeignKey(Authors, on_delete=models.CASCADE)
    PublicationYear = models.PositiveIntegerField()
    Categories = models.ManyToManyField(Category)
    Description = models.TextField()
    LanguageID = models.ForeignKey(Languages, on_delete=models.CASCADE)
    Price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cover_image = models.ImageField(upload_to = 'book/book_cover', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, null=True)
    IDENTIFIER_CHOICES = (
        ('ASIN', 'ASIN'),
        ('ISBN', 'ISBN'),
    )
    identifier_type = models.CharField(max_length=4, choices=IDENTIFIER_CHOICES, blank=True, null=True)
    identifier_value = models.CharField(max_length=20, blank=True, null=True) 
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
        # Delete associated reviews
        self.review_set.all().delete()
        super().delete(*args, **kwargs)

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'review')

class UserLibrary(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    books = models.ManyToManyField(Books, blank=True)

    def __str__(self):
        return f"Library of {self.user.username}"
    class Meta:
        verbose_name_plural = "User Libraries"