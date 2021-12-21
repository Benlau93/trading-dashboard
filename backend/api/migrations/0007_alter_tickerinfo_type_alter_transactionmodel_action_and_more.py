# Generated by Django 4.0 on 2021-12-19 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_alter_tickerinfo_currency_alter_tickerinfo_industry_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tickerinfo',
            name='type',
            field=models.CharField(db_column='ASSET_TYPE', max_length=20),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='action',
            field=models.CharField(choices=[('Buy', 'Buy'), ('Sell', 'Sell')], db_column='ACTION', max_length=5),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='date',
            field=models.DateField(db_column='DATE'),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='exchange_rate',
            field=models.FloatField(db_column='EXCHANGE_RATE'),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='fees',
            field=models.FloatField(db_column='FEES'),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='price',
            field=models.FloatField(db_column='PRICE'),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='quantity',
            field=models.FloatField(db_column='QUANTITY'),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='symbol',
            field=models.CharField(db_column='SYMBOL', max_length=20),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='value',
            field=models.FloatField(db_column='VALUE'),
        ),
        migrations.AlterField(
            model_name='transactionmodel',
            name='value_sgd',
            field=models.FloatField(db_column='VALUE_SGD'),
        ),
    ]
