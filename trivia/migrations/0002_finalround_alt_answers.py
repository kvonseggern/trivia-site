# Generated by Django 3.0.6 on 2020-05-13 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trivia', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='finalround',
            name='alt_answers',
            field=models.CharField(max_length=500, null=True),
        ),
    ]
