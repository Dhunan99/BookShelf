# Generated by Django 4.2.4 on 2023-09-10 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0018_alter_review_character_rating_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='overall_rating',
            field=models.FloatField(blank=True),
        ),
    ]
