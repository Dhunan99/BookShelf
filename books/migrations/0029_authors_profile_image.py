# Generated by Django 4.2.4 on 2023-09-13 17:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0028_authors_number_of_works'),
    ]

    operations = [
        migrations.AddField(
            model_name='authors',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='authors/'),
        ),
    ]