# Generated by Django 4.2.4 on 2023-09-16 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0033_remove_books_pdf_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='books',
            name='epub_file',
            field=models.FileField(blank=True, null=True, upload_to='book/epubs/'),
        ),
    ]
