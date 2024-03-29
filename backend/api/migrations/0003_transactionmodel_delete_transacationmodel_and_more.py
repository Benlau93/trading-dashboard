# Generated by Django 4.0 on 2021-12-19 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_rename_total_shares_openposition_total_quantity_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionModel',
            fields=[
                ('id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('date', models.DateField(db_column='Date')),
                ('symbol', models.CharField(db_column='Symbol', max_length=20)),
                ('action', models.CharField(choices=[('Buy', 'Buy'), ('Sell', 'Sell')], db_column='Action', max_length=5)),
                ('price', models.FloatField(db_column='Price')),
                ('quantity', models.FloatField(db_column='Quantity')),
                ('fees', models.FloatField(db_column='Fees')),
                ('exchange_rate', models.FloatField(db_column='Exchange Rate')),
                ('value', models.FloatField(db_column='Value')),
                ('value_sgd', models.FloatField(db_column='Value (SGD)')),
            ],
        ),
        migrations.DeleteModel(
            name='TransacationModel',
        ),
        migrations.AddField(
            model_name='openposition',
            name='unrealised_pl_per',
            field=models.FloatField(db_column='Unrealised P/L (%)', default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='date_close',
            field=models.DateField(db_column='Date_Close'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='date_open',
            field=models.DateField(db_column='Date_Open'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='holding',
            field=models.IntegerField(db_column='Holding (Days)'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='pl',
            field=models.FloatField(db_column='P/L'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='pl_per',
            field=models.FloatField(db_column='P/L (%)'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='pl_sgd',
            field=models.FloatField(db_column='P/L (SGD)'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='symbol',
            field=models.CharField(db_column='Symbol', max_length=20),
        ),
        migrations.AlterField(
            model_name='historicalpl',
            name='date',
            field=models.DateField(db_column='Date'),
        ),
        migrations.AlterField(
            model_name='historicalpl',
            name='pl_sgd',
            field=models.FloatField(db_column='P/L (SGD)'),
        ),
        migrations.AlterField(
            model_name='historicalpl',
            name='symbol',
            field=models.CharField(db_column='Symbol', max_length=20),
        ),
        migrations.AlterField(
            model_name='historicalpl',
            name='value_sgd',
            field=models.FloatField(db_column='Value (SGD)'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='avg_exchange_rate',
            field=models.FloatField(db_column='Avg Exchange Rate'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='avg_price',
            field=models.FloatField(db_column='Avg Price'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='current_value_sgd',
            field=models.FloatField(db_column='Value (SGD)'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='date_open',
            field=models.DateField(db_column='Date'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='symbol',
            field=models.CharField(db_column='Symbol', max_length=20),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='total_fees',
            field=models.FloatField(db_column='Total Fees'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='total_holding',
            field=models.IntegerField(db_column='Holding (Days)'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='total_quantity',
            field=models.FloatField(db_column='Total Quantity'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='total_value',
            field=models.FloatField(db_column='Total Value'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='total_value_sgd',
            field=models.FloatField(db_column='Total Value (SGD)'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='unrealised_pl',
            field=models.FloatField(db_column='Unrealised P/L'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='unrealised_pl_sgd',
            field=models.FloatField(db_column='Unrealised P/L (SGD)'),
        ),
        migrations.AlterField(
            model_name='openposition',
            name='weightage',
            field=models.FloatField(db_column='Weightage'),
        ),
        migrations.AlterField(
            model_name='tickerinfo',
            name='currency',
            field=models.CharField(db_column='Currency', max_length=10),
        ),
        migrations.AlterField(
            model_name='tickerinfo',
            name='industry',
            field=models.CharField(db_column='Industry', max_length=50),
        ),
        migrations.AlterField(
            model_name='tickerinfo',
            name='name',
            field=models.CharField(db_column='Name', max_length=50),
        ),
        migrations.AlterField(
            model_name='tickerinfo',
            name='sector',
            field=models.CharField(db_column='Sector', max_length=50),
        ),
        migrations.AlterField(
            model_name='tickerinfo',
            name='symbol',
            field=models.CharField(db_column='Symbol', max_length=20, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='tickerinfo',
            name='type',
            field=models.CharField(db_column='Asset Type', max_length=20),
        ),
    ]
