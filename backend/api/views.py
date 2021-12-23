from rest_framework import serializers, status
from rest_framework.views import APIView
from datetime import date
from datetime import datetime
from .serializers import TransactionSerializer, TickerSerializer, OpenSerializer, ClosedSerializer
from rest_framework.response import Response
from .models import TransactionModel, TickerInfo, OpenPosition
import yfinance as yf
import numpy as np

class TransactionViews(APIView):
    transaction_serializer = TransactionSerializer
    ticker_serializer = TickerSerializer
    open_serializer = OpenSerializer
    close_serializer = ClosedSerializer

    def get(self, request, format=None):
        data = TransactionModel.objects.all()
        serializer = self.transaction_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        data = request.data.dict()
        verbose = {}

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
                open_position = open_position[0]
                open_serialized = self.open_serializer(open_position)
                update_data = open_serialized.data
                # there is open position, update to open position

                # check if add on or close position
                if data["action"] == "Buy":
                    
                    # update
                    total_quantity = update_data["total_quantity"] + data["quantity"]
                    avg_price = ((update_data["total_quantity"] * update_data["avg_price"]) + (data["price"] * data["quantity"])) / total_quantity
                    avg_exchange_rate = ((update_data["total_quantity"] * update_data["avg_exchange_rate"]) + (data["exchange_rate"] * data["quantity"])) / total_quantity
                    update_data.update({"total_quantity":total_quantity,
                                "avg_price":avg_price,
                                "total_fees":update_data["total_fees"] + data["fees"],
                                "avg_exchange_rate":avg_exchange_rate,
                                "total_value":update_data["total_value"] + data["value"],
                                "total_value_sgd":update_data["total_value_sgd"] + data["value_sgd"]})
                    open_serialized = self.open_serializer(open_position,data=update_data)
                    if open_serialized.is_valid():
                        open_serialized.save()
                        verbose = {"verbose":f"Updated Existing Position, increased {update_data['symbol']} to {update_data['total_quantity']} with average price of ${round(update_data['avg_price'],2)}."}
                    else:
                        return Response(verbose,status=status.HTTP_400_BAD_REQUEST)
                else:
                    # close position

                    # check if close all
                    if update_data["total_quantity"] < data["quantity"]:
                        verbose = {"verbose":"Invalid transaction. Please ensure you have sufficient quantity"}
                        return Response(verbose,status=status.HTTP_400_BAD_REQUEST)
                    elif update_data["total_quantity"] == data["quantity"]:
                        # add to closed position
                        id = open_position.id + "|" + date_str
                        holding = (date_ - open_position.date_open).days
                        pl = data["value"] - open_position.total_value
                        pl_sgd = data["value_sgd"] - open_position.total_value_sgd
                        pl_per = pl_sgd / open_position.total_value_sgd
                        closed_data = {"id":id,
                                        "symbol":data["symbol"],
                                        "date_open":open_position.date_open,
                                        "date_close":date_,
                                        "holding":holding,
                                        "pl":pl,
                                        "pl_sgd":pl_sgd,
                                        "pl_per":pl_per}

                        closed_serialized = self.close_serializer(data=closed_data)
                        if closed_serialized.is_valid():
                            # add closed position
                            closed_serialized.save()
                            
                            # delete open position
                            open_position.delete()
                            
                            verbose = {"verbose":f"Closed a Position, closed {data['symbol']} with P/L of ${round(pl_sgd,2)}"}
                        else:
                            return Response(verbose,status=status.HTTP_400_BAD_REQUEST)
                        
                    else:
                        # close some
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
                    open_serialized.save()
                    verbose = {"verbose":f"Opened New Position, {data['quantity']} of {data['symbol']} at ${data['price']}."}
                else:
                    return Response(verbose,status=status.HTTP_400_BAD_REQUEST)

            return Response(verbose, status = status.HTTP_200_OK)
        else:

            return Response(verbose, status=status.HTTP_400_BAD_REQUEST)