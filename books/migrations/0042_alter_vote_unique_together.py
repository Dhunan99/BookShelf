# Generated by Django 4.2.4 on 2024-02-21 16:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0041_alter_vote_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set(),
        ),
    ]