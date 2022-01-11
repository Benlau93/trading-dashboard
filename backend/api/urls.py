from django.urls import path, include
from .views import TransactionViews, TickerViews, ClosedViews, OpenViews, HistoricalViews, RefreshViews, DownloadViews

urlpatterns = [
    path('transaction', TransactionViews.as_view()),
    path('ticker', TickerViews.as_view()),
    path('closed', ClosedViews.as_view()),
    path('open', OpenViews.as_view()),
    path('historical', HistoricalViews.as_view()),
    path('refresh', RefreshViews.as_view()),
    path("download", DownloadViews.as_view())
]
