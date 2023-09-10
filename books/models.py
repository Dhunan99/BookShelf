# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Authors(models.Model):
    Author = models.AutoField(primary_key=True)
    AuthorName = models.CharField(max_length=100)
    Biography = models.TextField(blank=True, null=True)
    SocialMediaLinks = models.CharField(max_length=200, blank=True, null=True)
    class Meta:
        verbose_name_plural = "Authors"
    def __str__(self):
        return self.AuthorName

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
    class Meta:
        verbose_name_plural = "Books"
    def __str__(self):
        return self.Title

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

    class Meta:
        # Add a unique constraint to ensure one review per user per book
        unique_together = ('user', 'book')

    def __str__(self):
        return f"Review from '{self.user.username}' for '{self.book.Title}' by '{self.book.Author}'"