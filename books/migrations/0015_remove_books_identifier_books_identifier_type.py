# Generated by Django 4.2.4 on 2023-09-03 03:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0014_remove_books_identifiers_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='books',
            name='identifier',
        ),
        migrations.AddField(
            model_name='books',
            name='identifier_type',
            field=models.CharField(blank=True, choices=[('ASIN', 'ASIN'), ('ISBN', 'ISBN')], max_length=4, null=True),
        ),
    ]