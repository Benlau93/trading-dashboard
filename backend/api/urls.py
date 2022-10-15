from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViews, TickerViewSet, ClosedViewSet, OpenViewSet, HistoricalViewSet, RefreshViews, DownloadViews, RefreshDividend, DividendViewSet, WatchlistView, WatchlistRefreshView

# create router
router = DefaultRouter()
router.register(r'ticker', TickerViewSet,basename="ticker")
router.register(r'closed', ClosedViewSet,basename="closed")
router.register(r'open', OpenViewSet,basename="open")
router.register(r'historical', HistoricalViewSet,basename="historical")
router.register(r'dividend', DividendViewSet,basename="dividend")


urlpatterns = [
    path("", include(router.urls)),
    path('transaction', TransactionViews.as_view()),
    path('refresh', RefreshViews.as_view()),
    path("download", DownloadViews.as_view()),
    path("refresh-dividend", RefreshDividend.as_view()),
    path("watchlist",WatchlistView.as_view()),
    path("refresh-watchlist", WatchlistRefreshView.as_view())
]
