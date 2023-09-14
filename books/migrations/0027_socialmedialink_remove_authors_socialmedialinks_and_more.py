# Generated by Django 4.2.4 on 2023-09-12 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0026_rename_category_books_categories'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialMediaLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform', models.CharField(choices=[('twitter', 'Twitter'), ('facebook', 'Facebook'), ('instagram', 'Instagram')], max_length=20)),
                ('link', models.URLField()),
            ],
        ),
        migrations.RemoveField(
            model_name='authors',
            name='SocialMediaLinks',
        ),
        migrations.AddField(
            model_name='authors',
            name='social_media_links',
            field=models.ManyToManyField(blank=True, to='books.socialmedialink'),
        ),
    ]
