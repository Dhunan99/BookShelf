# Generated by Django 4.2.4 on 2023-08-17 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0002_books_cover_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='books',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='book/book_cover'),
        ),
    ]
