# Generated by Django 4.2.4 on 2023-09-02 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0008_category_alter_books_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='books',
            name='Category',
        ),
        migrations.AddField(
            model_name='books',
            name='Categories',
            field=models.ManyToManyField(to='books.category'),
        ),
    ]
