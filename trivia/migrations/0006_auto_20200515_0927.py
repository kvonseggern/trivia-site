# Generated by Django 3.0.6 on 2020-05-15 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trivia', '0005_question_round'),
    ]

    operations = [
        migrations.AlterField(
            model_name='finalresponse',
            name='wager',
            field=models.IntegerField(default=None, null=True),
        ),
    ]
