# Generated by Django 4.2.4 on 2023-08-17 16:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Authors',
            fields=[
                ('AuthorID', models.AutoField(primary_key=True, serialize=False)),
                ('AuthorName', models.CharField(max_length=100)),
                ('Biography', models.TextField(blank=True, null=True)),
                ('SocialMediaLinks', models.CharField(blank=True, max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Languages',
            fields=[
                ('LanguageID', models.AutoField(primary_key=True, serialize=False)),
                ('LanguageName', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Books',
            fields=[
                ('BookID', models.AutoField(primary_key=True, serialize=False)),
                ('Title', models.CharField(max_length=200)),
                ('ISBN', models.BigIntegerField(blank=True, null=True)),
                ('PublicationDate', models.DateTimeField()),
                ('Category', models.CharField(max_length=100)),
                ('Description', models.TextField()),
                ('Price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('AuthorID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.authors')),
                ('LanguageID', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='books.languages')),
            ],
        ),
    ]
