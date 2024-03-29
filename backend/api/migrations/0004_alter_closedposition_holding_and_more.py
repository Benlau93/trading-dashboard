# Generated by Django 4.0 on 2021-12-19 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_transactionmodel_delete_transacationmodel_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='closedposition',
            name='holding',
            field=models.IntegerField(db_column='Holding_Days'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='pl_per',
            field=models.FloatField(db_column='P/L_%'),
        ),
        migrations.AlterField(
            model_name='closedposition',
            name='pl_sgd',
            field=models.FloatField(db_column='P/L_SGD'),
        ),
    ]
