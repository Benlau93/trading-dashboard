from rest_framework import serializers, status
from rest_framework.views import APIView
from datetime import date
from datetime import datetime
from .serializers import TransactionSerializer, TickerSerializer, OpenSerializer
from rest_framework.response import Response
from .models import TransactionModel, TickerInfo, OpenPosition
import yfinance as yf
import numpy as np

class TransactionViews(APIView):
    transaction_serializer = TransactionSerializer
    ticker_serializer = TickerSerializer
    open_serializer = OpenSerializer

    def get(self, request, format=None):
        data = TransactionModel.objects.all()
        serializer = self.transaction_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        data = request.data.dict()

        # formating
        data["price"], data["quantity"], data["fees"], data["exchange_rate"] = float(data["price"]), float(data["quantity"]), float(data["fees"]), float(data["exchange_rate"])
        data["symbol"] = data["symbol"].upper()
        date_ = datetime.strptime(data["date"],"%Y-%m-%d")
        date_ = date(date_.year, date_.month, date_.day)
        date_str = data["date"]

        # transformation
        data["value"] = data["price"] * data["quantity"] + (-data["fees"] if data["action"]=="Sell" else data["fees"])
        data["value_sgd"] = data["value"] * data["exchange_rate"]
        data["id"] = data["symbol"] + "|" + date_str + "|" + data["action"]

        # update data
        data.update({
                    "date":date_})

        transaction_serialised = self.transaction_serializer(data=data)

        # check if post data is valid
        if transaction_serialised.is_valid():
            print("CREATED NEW TRANSACTION")
            # transaction_serialised.save()
            # check if ticker in ticker info
            query = TickerInfo.objects.filter(symbol=data["symbol"])

            if len(query) == 0:
                # save ticker information in tickerinfo if not present
                ticker = yf.Ticker(data["symbol"]).info
                ticker_data = {
                    "symbol":data["symbol"],
                    "name":ticker["shortName"],
                    "type":ticker["quoteType"],
                    "currency":ticker["currency"],
                    "sector": np.nan if ticker["quoteType"] != "EQUITY" else ticker["sector"],
                    "industry": np.nan if ticker["quoteType"] != "EQUITY" else ticker["industry"]
                }
                ticker_serialized = self.ticker_serializer(data=ticker_data)
                if ticker_serialized.is_valid():
                    # ticker_serialized.save()
                    print("CREATED NEW TICKER INFO")
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

            # check if there is open position
            open_position = OpenPosition.objects.filter(symbol=data["symbol"])

            if len(open_position)==1:
                # there is open position, update to open position
                print("THERE IS OPEN")
                pass

            else:
                # there is no open position, create new open position
                open_data = {
                    "id": data["symbol"] + "|" + date_str,
                    "symbol": data["symbol"],
                    "date_open": date_,
                    'avg_price': data["price"],
                    "total_quantity": data["quantity"],
                    "total_fees": data["fees"],
                    "avg_exchange_rate": data["exchange_rate"],
                    "total_value": data["value"],
                    "total_value_sgd": data["value_sgd"],
                    "total_holding": (date.today() - date_).days,
                    "unrealised_pl": 0,
                    "unrealised_pl_sgd":0,
                    "unrealised_pl_per":0,
                    "current_value_sgd":0
                }
                open_serialized = self.open_serializer(data=open_data)
                if open_serialized.is_valid():
                    # open_serialized.save()
                    print("CREATED NEW OPEN POSITION")
                else:
                    return Response(status=status.HTTP_400_BAD_REQUEST)

            return Response(status = status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)