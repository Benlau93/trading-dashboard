from rest_framework import serializers, status
from rest_framework.views import APIView
from datetime import date
from datetime import datetime
from .serializers import TransactionSerializer, TickerSerializer, OpenSerializer, ClosedSerializer, HistoricalSerializer, DividendSerializer, WatchlistSerializer
from rest_framework.response import Response
from .models import TransactionModel, TickerInfo, OpenPosition, ClosedPosition, HistoricalPL, Dividend, Watchlist
import yfinance as yf
import numpy as np
import pandas as pd

class DownloadViews(APIView):

    def post(self, request, format=None):
        data = request.data
        df = yf.download(tickers=data["symbol"], start=data["start_date"], end=date.today(),interval=data["interval"])
        df["Symbol"] = data["symbol"]
        df = df.reset_index()
        return Response(df.to_dict(orient="records"), status=status.HTTP_200_OK)

class TickerViews(APIView):
    ticker_serializer = TickerSerializer

    def get(self, request, format=None):
        data = TickerInfo.objects.all()
        serializer = self.ticker_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClosedViews(APIView):
    close_serializer = ClosedSerializer

    def get(self, request, format=None):
        data = ClosedPosition.objects.all()
        serializer = self.close_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OpenViews(APIView):
    open_serializer = OpenSerializer

    def get(self, request, format=None):
        data = OpenPosition.objects.all()
        serializer = self.open_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class HistoricalViews(APIView):
    hist_serializer = HistoricalSerializer

    def get(self, request, format=None):
        data = HistoricalPL.objects.all()
        serializer = self.hist_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DividendViews(APIView):
    dividend_serializer = DividendSerializer

    def get(self, request, format=None):
        data = Dividend.objects.all()
        serializer = self.dividend_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        data["fees"] = data["fees"] * data["exchange_rate"]
        data["id"] = data["symbol"] + "|" + date_str + "|" + data["action"]

        # update data
        data.update({
                    "date":date_})

        transaction_serialised = self.transaction_serializer(data=data)

        # check if post data is valid
        if transaction_serialised.is_valid():
            print("CREATED NEW TRANSACTION")
            transaction_serialised.save()
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
                    ticker_serialized.save()
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
                    
                    # check if valid quantity
                    if open_position.total_quantity < data["quantity"]:
                        verbose = {"verbose":"Invalid transaction. Please ensure you have sufficient quantity"}
                        return Response(verbose,status=status.HTTP_400_BAD_REQUEST)
                    else:

                        
                        new_qty = open_position.total_quantity - data["quantity"]

                        if new_qty == 0:
                            # close all position
                            id = open_position.id + "|" + date_str
                        else:
                            id = open_position.id
                            update_data.update({
                                "total_quantity":new_qty,
                                "total_fees": open_position.total_fees + data["fees"],
                                "total_value":open_position.total_value / open_position.total_quantity * new_qty,
                                "total_value_sgd":open_position.total_value_sgd / open_position.total_quantity * new_qty
                            })
                        
                        # add to closed position
                        
                        holding = (date_ - open_position.date_open).days
                        pl = data["value"] - (open_position.total_value / open_position.total_quantity * data["quantity"])
                        pl_sgd = data["value_sgd"] - (open_position.total_value_sgd / open_position.total_quantity * data["quantity"])
                        pl_per = pl_sgd / (open_position.total_value_sgd / open_position.total_quantity * data["quantity"])


                        
                        # check if existing partial closed position
                        closed_position = ClosedPosition.objects.filter(pk=open_position.id)

                        if len(closed_position) == 1:
                            closed_position = closed_position[0]
                            closed_serialized = self.close_serializer(closed_position)
                            closed_data = closed_serialized.data
                            closed_data.update({
                                "id":id,
                                "date_close":date_,
                                "holding":holding,
                                "pl":closed_position.pl + pl,
                                "pl_sgd": closed_position.pl_sgd + pl_sgd
                            })
                            closed_data.update({"pl_per":closed_data["pl_sgd"] / closed_data["value_sgd_open"]})

                            # delete closed object if complete close
                            if new_qty == 0:
                                closed_position.delete()

                        else:
                            closed_position = None
                            closed_data = {"id":id,
                                            "symbol":data["symbol"],
                                            "date_open":open_position.date_open,
                                            "date_close":date_,
                                            "holding":holding,
                                            "pl":pl,
                                            "pl_sgd":pl_sgd,
                                            "pl_per":pl_per,
                                            "value_sgd_open":open_position.total_value_sgd}

                        closed_serialized = self.close_serializer(closed_position, data=closed_data)
                        if closed_serialized.is_valid():
                            # add closed position
                            closed_serialized.save()

                            if new_qty == 0:
                                # delete open position
                                open_position.delete()
                                verbose = {"verbose":f"Closed a Position, closed {data['symbol']} with P/L of ${round(pl_sgd,2)}"}
                            else:
                                # update open position
                                open_serialized = self.open_serializer(open_position,data=update_data)
                                if open_serialized.is_valid():
                                    open_serialized.save()
                                    verbose = {"verbose":f"Partially Closed a Position, closed {data['quantity']} of {data['symbol']} with P/L of ${round(pl_sgd,2)}"}
                                else:
                                    return Response(verbose,status=status.HTTP_400_BAD_REQUEST)
                        else:
                            return Response(verbose,status=status.HTTP_400_BAD_REQUEST)
                    

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


class RefreshViews(APIView):
    hist_serializer = HistoricalSerializer

    def get(self, request, format=None):

        # get all open position data
        open_position = OpenPosition.objects.all().values("symbol","date_open","total_quantity","avg_price","avg_exchange_rate","total_fees","total_value_sgd")
        open_position = pd.DataFrame(open_position)
        
        # get list of open position symbol
        symbol_list = open_position["symbol"].unique().tolist()
        symbol_list = " ".join(symbol_list)

        # get earliest date
        min_date = open_position["date_open"].min()

        # # download yfinance price
        data = yf.download(symbol_list, start = min_date, interval="1d", group_by="ticker", progress=False).reset_index()
        data = data.melt(id_vars="Date", var_name=["symbol","OHLC"], value_name="price")
        data = data[data["OHLC"]=="Close"].drop(["OHLC"],axis=1)

        # get daily P/L
        historical = pd.merge(open_position,data,on="symbol").dropna()
        historical = historical[historical["Date"]>=historical["date_open"]].copy()
        historical["pl_sgd"] = ((historical["price"] * historical["total_quantity"]) * (historical["avg_exchange_rate"])) - historical["total_value_sgd"]
        historical = historical[["Date","symbol","pl_sgd","price"]].copy()
        historical.columns = historical.columns.str.lower()

       

        
        # delete exisitng historical data
        exist = HistoricalPL.objects.all().delete()

        # insert into historical model
        df_records = historical.to_dict(orient="records")
        model_instances = [HistoricalPL(
        date = record["date"],
        symbol = record["symbol"],
        price = record["price"],
        pl_sgd = record["pl_sgd"],
        ) for record in df_records]
        HistoricalPL.objects.bulk_create(model_instances)

        return Response(status=status.HTTP_200_OK)


class RefreshDividend(APIView):
    # serializer
    dividend_serializer = DividendSerializer

    def get(self, request, format=None):


        def adjust_dividend(row):
            dividend = row["dividend_value"]
        
            if row["latest_exchange_rate"] != 1:
                # account for 30% US tax
                dividend = dividend * 0.7

                # account for FSMone dividend handling fees
                if row["date_dividend"] < pd.to_datetime("15-03-2021"):
                    dividend -= (2.5*1.07)
                
                # account for exchange rate
                dividend = dividend * row["latest_exchange_rate"]

            
            return max(0,dividend)
        
        # get current open position
        open_position = OpenPosition.objects.all().values("symbol","date_open","total_quantity","total_value_sgd","avg_exchange_rate")
        open_position = pd.DataFrame(open_position)

        # get latest dividend (use csv first)
        dividend_hist = Dividend.objects.all().values("symbol","date_dividend")
        dividend_hist = pd.DataFrame(dividend_hist)
        dividend_hist = dividend_hist.sort_values(["symbol","date_dividend"]).groupby("symbol").tail(1)

        # merge open and historical dividend
        df = pd.merge(open_position, dividend_hist, on="symbol", how="left")
        df["DATE"] = df.apply(lambda row: row["date_open"] if pd.isnull(row["date_dividend"]) else row["date_dividend"], axis=1)
        df = df.drop(["date_dividend","date_open"], axis=1)
        # get dividend from yf
        symbols = " ".join(open_position["symbol"].unique())
        tickers = yf.Tickers(symbols)

        # get dividend table
        dividend = pd.DataFrame()

        for k,v in tickers.tickers.items():
            _ = pd.DataFrame(v.dividends).reset_index()
            _["symbol"] = k

            # append to main
            dividend = dividend.append(_, sort=True, ignore_index=True)

        # format date
        dividend["Date"] = pd.to_datetime(dividend["Date"])
        dividend = dividend.rename({"Date":"date_dividend"}, axis=1)

        # filter to new dividend not in DB
        dividend = pd.merge(dividend, df, on="symbol")
        dividend = dividend[dividend["date_dividend"]>dividend["DATE"]].copy()

        # check if there is new dividend
        if len(dividend) > 0:

            # get latest exchange rate
            exchange_rate = yf.download("SGDUSD=X", period = "6mo", interval="1d",progress=False)
            exchange_rate = exchange_rate[["Close"]].reset_index()

            us_stock = dividend[dividend["avg_exchange_rate"]>1][["symbol","date_dividend"]].copy()
            exchange_rate = pd.merge(us_stock, exchange_rate, how="cross")
            exchange_rate = exchange_rate[exchange_rate["Date"]<=exchange_rate["date_dividend"]].sort_values(["symbol","date_dividend","Date"]).groupby(["symbol","date_dividend"]).tail(1)
            exchange_rate["latest_exchange_rate"] = exchange_rate["Close"].map(lambda x: 1/x)
            exchange_rate = exchange_rate.drop(["Date","Close"], axis=1)

            # merge back to dividend
            dividend = pd.merge(dividend, exchange_rate, on=["symbol","date_dividend"], how="left")
            dividend["latest_exchange_rate"] = dividend["latest_exchange_rate"].fillna(1)

            # format dividend
            dividend["dividend_value"] = dividend["Dividends"] * dividend["total_quantity"]
            dividend["dividend_adjusted"] = dividend.apply(adjust_dividend, axis=1)

            # remove 0 dividend
            dividend = dividend[dividend["dividend_adjusted"]>0].copy()

            # check if there is positive dividend
            if len(dividend) >0:

                # get dividend yield
                dividend["dividend_per"] = dividend["dividend_adjusted"] / dividend["total_value_sgd"]

                # get ID
                dividend["id"] = dividend["symbol"] + "|" + dividend["date_dividend"].astype(str) + "|" + dividend["Dividends"].astype(str)

                # ingest into dividend model
                df_records = dividend.to_dict(orient="records")
                model_instances = [Dividend(
                id = record["id"],
                symbol = record["symbol"],
                date_dividend = record["date_dividend"],
                dividends = record["Dividends"],
                total_quantity = record["total_quantity"],
                total_value_sgd = record["total_value_sgd"],
                latest_exchange_rate = record["latest_exchange_rate"],
                dividend_value = record["dividend_value"],
                dividend_adjusted = record["dividend_adjusted"],
                dividend_per = record["dividend_per"],
                ) for record in df_records]
                Dividend.objects.bulk_create(model_instances)

        return Response(status=status.HTTP_200_OK)

class WatchlistView(APIView):
    # serializer
    watch_serializer = WatchlistSerializer

    # get watchlist data from db
    def get(self, request, format=None):
        data = Watchlist.objects.all()
        serializer = self.watch_serializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
    # add to watchlist
    def post(self, request, format=None):
        data = request.data.dict()
        data["symbol"] = data["symbol"].upper()
        symbol = data["symbol"]

        # get ticker from yahoo finance
        ticker = yf.Ticker(symbol)

        # check if ticker is valid
        if len(ticker.info) <= 3:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # check if ticker is present in model
        exist  = Watchlist.objects.filter(pk=symbol)
        if len(exist) == 1:
            exist.delete()

        # get latest price
        current_price = ticker.history(period="3d")["Close"].reset_index()
        current_price = current_price[current_price["Date"]==current_price["Date"].max()]["Close"].iloc[0]

         # add to data
        data.update({"name":ticker.info["shortName"],
                    "current_price":current_price})

        watch_serialized = self.watch_serializer(data=data)
        if watch_serialized.is_valid():
            watch_serialized.save()

            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # delete from watchlist
    def delete(self, request, format=None):
        pk = request.data["pk"]
        watch = Watchlist.objects.filter(pk=pk)

        if len(watch) == 1:
            watch.delete()
        
        return Response(status=status.HTTP_200_OK)

class WatchlistRefreshView(APIView):
    # serializer
    watch_serializer = WatchlistSerializer

    def get(self, request, format=None):
        # get all ticker
        symbol_list = Watchlist.objects.all().values("symbol")
        symbol_list = [v["symbol"] for v in symbol_list.values()]
        symbol_str = " ".join(symbol_list)

        # download yfinance price
        data = yf.download(symbol_str, period="5d", group_by="ticker", progress=False).reset_index().dropna()
        data = data.melt(id_vars="Date", var_name=["symbol","OHLC"], value_name="price")
        data = data[data["OHLC"]=="Close"].drop(["OHLC"],axis=1)
        
        # get latest date for each symbol
        data = data.sort_values(["symbol","Date"]).groupby("symbol").tail(1)
        data = data[["symbol","price"]].set_index("symbol").to_dict()

        # update current price of each symbol
        for sym in symbol_list:
            obj = Watchlist.objects.get(symbol=sym)
            obj.current_price = data["price"][sym]
            obj.save()

        return Response(status=status.HTTP_200_OK)