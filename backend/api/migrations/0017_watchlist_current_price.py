# Generated by Django 4.0 on 2022-08-18 01:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_remove_watchlist_current_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='watchlist',
            name='current_price',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
    ]
