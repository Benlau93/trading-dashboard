from django.urls import path, include
from .views import BenchmarksView, TransactionViews, TickerViews, ClosedViews, OpenViews, HistoricalViews, RefreshViews, DownloadViews, RefreshDividend, DividendViews, WatchlistView, WatchlistRefreshView


urlpatterns = [
    path("benchmark/<str:market>", BenchmarksView.as_view()),
    path('transaction', TransactionViews.as_view()),
    path('ticker', TickerViews.as_view()),
    path('closed', ClosedViews.as_view()),
    path('open', OpenViews.as_view()),
    path('historical', HistoricalViews.as_view()),
    path('refresh', RefreshViews.as_view()),
    path("download", DownloadViews.as_view()),
    path("refresh-dividend", RefreshDividend.as_view()),
    path("dividend", DividendViews.as_view()),
    path("watchlist",WatchlistView.as_view()),
    path("refresh-watchlist", WatchlistRefreshView.as_view())
]
