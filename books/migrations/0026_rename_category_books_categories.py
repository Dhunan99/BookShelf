# Generated by Django 4.2.4 on 2023-09-11 17:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0025_rename_genre_books_category'),
    ]

    operations = [
        migrations.RenameField(
            model_name='books',
            old_name='Category',
            new_name='Categories',
        ),
    ]
