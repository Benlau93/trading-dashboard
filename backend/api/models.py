from pickle import FALSE
from django.db import models

# Create your models here.
class TickerInfo(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True, db_column="SYMBOL")
    name = models.CharField(max_length=50, blank=False, db_column="NAME")
    type = models.CharField(max_length=20, blank=False, db_column="ASSET_TYPE")
    currency = models.CharField(max_length=10, blank=False, db_column="CURRENCY")
    sector = models.CharField(max_length=50, db_column="SECTOR")
    industry = models.CharField(max_length=50, db_column="INDUSTRY")

class TransactionModel(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    date = models.DateField(blank=False, db_column="DATE")
    symbol = models.CharField(max_length=20, blank=False, db_column="SYMBOL")
    action = models.CharField(max_length=5, choices= [("Buy","Buy"), ("Sell","Sell")], blank=False,db_column="ACTION")
    price = models.FloatField(blank=False, db_column="PRICE")
    quantity = models.FloatField(blank=False, db_column="QUANTITY")
    fees = models.FloatField(blank=False, db_column="FEES")
    exchange_rate = models.FloatField(blank=False, db_column="EXCHANGE_RATE")
    value = models.FloatField(blank=False, db_column="VALUE")
    value_sgd = models.FloatField(blank=False, db_column="VALUE_SGD")


class ClosedPosition(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    symbol = models.CharField(max_length=20, blank=False, db_column="SYMBOL")
    date_open = models.DateField(blank=False, db_column="DATE_OPEN")
    date_close = models.DateField(blank=False, db_column="DATE_CLOSE")
    holding = models.IntegerField(blank = False, db_column="HOLDING_DAY")
    pl = models.FloatField(blank=False, db_column="PL")
    pl_sgd = models.FloatField(blank=False, db_column="PL_SGD")
    pl_per = models.FloatField(blank=False, db_column="PL_PERCENTAGE")
    value_sgd_open = models.FloatField(blank=False, default=0, db_column="VALUE_SGD_OPEN")

class OpenPosition(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    symbol = models.CharField(max_length=20, blank=False,db_column="SYMBOL")
    date_open = models.DateField(blank=False, db_column="DATE")
    avg_price = models.FloatField(blank = False, db_column="AVG_PRICE")
    total_quantity = models.FloatField(blank = False, db_column="TOTAL_QUANTITY")
    total_fees = models.FloatField(blank = False, db_column="TOTAL_FEES")
    avg_exchange_rate = models.FloatField(blank = False, db_column="AVG_EXCHANGE_RATE")
    total_value = models.FloatField(blank = False, db_column="TOTAL_VALUE")
    total_value_sgd = models.FloatField(blank = False, db_column="TOTAL_VALUE_SGD")


class HistoricalPL(models.Model):
    date = models.DateField(blank=False, db_column="DATE")
    symbol = models.CharField(max_length=20, blank=False, db_column="SYMBOL")
    price = models.FloatField(blank = False, db_column="PRICE", default=0)
    pl_sgd = models.FloatField(blank = False, db_column="PL_SGD")


class Dividend(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    symbol = models.CharField(max_length=20, blank=False)
    date_dividend = models.DateField(blank=False)
    dividends = models.FloatField(blank=False)
    total_quantity = models.FloatField(blank=False)
    total_value_sgd = models.FloatField(blank=False)
    latest_exchange_rate = models.FloatField(blank=False)
    dividend_value = models.FloatField(blank=False)
    dividend_adjusted = models.FloatField(blank=False)
    dividend_per = models.FloatField(blank=False)

class Watchlist(models.Model):
    symbol = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100, blank=False)
    current_price = models.FloatField(blank=False)
    target_price = models.FloatField(blank=False)
    direction = models.CharField(max_length=10, choices=[("Above","Above"), ("Below","Below")], blank=False)