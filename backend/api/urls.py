from django.urls import path, include
from yfinance.ticker import Ticker
from .views import TransactionViews, TickerViews, ClosedViews, OpenViews, HistoricalViews, RefreshViews

urlpatterns = [
    path('transaction', TransactionViews.as_view()),
    path('ticker', TickerViews.as_view()),
    path('closed', ClosedViews.as_view()),
    path('open', OpenViews.as_view()),
    path('historical', HistoricalViews.as_view()),
    path('refresh', RefreshViews.as_view())
]
