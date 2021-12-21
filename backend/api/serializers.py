from rest_framework import serializers
from .models import OpenPosition, TransactionModel, TickerInfo
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