# Generated by Django 3.0.6 on 2020-05-17 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trivia', '0006_auto_20200515_0927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='finalround',
            name='status',
            field=models.CharField(choices=[('0', 'Not Open'), ('1', 'Wager'), ('2', 'Answer Time'), ('3', 'Check Answers'), ('4', 'Closed')], default=0, max_length=1),
        ),
    ]