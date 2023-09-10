# Generated by Django 4.2.4 on 2023-08-18 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0006_alter_books_publicationdate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='books',
            name='PublicationDate',
        ),
        migrations.AddField(
            model_name='books',
            name='PublicationYear',
            field=models.PositiveIntegerField(default=2001),
            preserve_default=False,
        ),
    ]
