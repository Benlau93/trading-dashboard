from rest_framework import serializers
from .models import OpenPosition, TransactionModel, TickerInfo, ClosedPosition, HistoricalPL, Dividend, Watchlist, Benchmarks
import yfinance as yf

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionModel
        fields = "__all__"

    def validate_symbol(self, value):
        val_ticker = yf.Ticker(value.upper())
        if len(val_ticker.info) <= 3:
            raise serializers.ValidationError("Ticker not found in yahoo finance")
        else:
            return value.upper()

    def create(self, validated_data):
        return TransactionModel.objects.create(**validated_data)


class TickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TickerInfo
        fields = "__all__"
    
    def create(self, validated_data):
        return TickerInfo.objects.create(**validated_data)

class OpenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenPosition
        fields = "__all__"

    def create(self, validated_data):
        return OpenPosition.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.total_quantity = validated_data.get('total_quantity', instance.total_quantity)
        instance.avg_price = validated_data.get('avg_price', instance.avg_price)
        instance.total_fees = validated_data.get('total_fees', instance.total_fees)
        instance.avg_exchange_rate = validated_data.get('avg_exchange_rate', instance.avg_exchange_rate)
        instance.total_value = validated_data.get('total_value', instance.total_value)
        instance.total_value_sgd = validated_data.get('total_value_sgd', instance.total_value_sgd)
        instance.save()
        return instance

class ClosedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClosedPosition
        fields = "__all__"

        def create(self, validated_data):
            return ClosedPosition.objects.create(**validated_data)
        
        def update(self, instance, validated_data):
            instance.id = validated_data.get('id', instance.id)
            instance.date_close = validated_data.get('date_close', instance.date_close)
            instance.holding = validated_data.get('holding', instance.holding)
            instance.pl = validated_data.get('pl', instance.pl)
            instance.pl_sgd = validated_data.get('pl_sgd', instance.pl_sgd)
            instance.value_sgd = validated_data.get('value_sgd', instance.value_sgd)
            instance.save()
            return instance


class HistoricalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricalPL
        fields = "__all__"

    def create(self, validated_data):
        return HistoricalPL.objects.create(**validated_data)

class DividendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dividend
        fields = "__all__"

    def create(self, validated_data):
        return Dividend.objects.create(**validated_data)


class WatchlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Watchlist
        fields = "__all__"

    def create(self, validated_data):
        return Watchlist.objects.create(**validated_data)


class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmarks
        fields = "__all__"