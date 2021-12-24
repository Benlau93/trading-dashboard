from django.contrib import admin
from .models import TransactionModel, OpenPosition, ClosedPosition, TickerInfo

# Register your models here.
admin.site.register(TickerInfo)
admin.site.register(TransactionModel)
admin.site.register(OpenPosition)
admin.site.register(ClosedPosition)