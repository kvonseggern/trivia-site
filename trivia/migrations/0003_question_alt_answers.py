# Generated by Django 3.0.6 on 2020-05-13 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trivia', '0002_finalround_alt_answers'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='alt_answers',
            field=models.CharField(max_length=500, null=True),
        ),
    ]
