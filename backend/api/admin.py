from django.contrib import admin
from .models import TransactionModel, OpenPosition, ClosedPosition, TickerInfo, HistoricalPL, Dividend, Watchlist

# Register your models here.
admin.site.register(TickerInfo)
admin.site.register(TransactionModel)
admin.site.register(OpenPosition)
admin.site.register(ClosedPosition)
admin.site.register(HistoricalPL)
admin.site.register(Dividend)
admin.site.register(Watchlist)