# Create your models here.
from django.db import models

class Authors(models.Model):
    AuthorID = models.AutoField(primary_key=True)
    AuthorName = models.CharField(max_length=100)
    Biography = models.TextField(blank=True, null=True)
    SocialMediaLinks = models.CharField(max_length=200, blank=True, null=True)

class Languages(models.Model):
    LanguageID = models.AutoField(primary_key=True)
    LanguageName = models.CharField(max_length=50)

class Books(models.Model):
    BookID = models.AutoField(primary_key=True)
    Title = models.CharField(max_length=200)
    AuthorID = models.ForeignKey(Authors, on_delete=models.CASCADE)
    ISBN = models.BigIntegerField(blank=True, null=True)
    PublicationDate = models.DateTimeField()
    Category = models.CharField(max_length=100)
    Description = models.TextField()
    LanguageID = models.ForeignKey(Languages, on_delete=models.CASCADE)
    Price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cover_image = models.ImageField(upload_to = 'book/book_cover', blank=True, null=True)
