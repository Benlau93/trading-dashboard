from django.urls import path, include
from .views import TransactionViews

urlpatterns = [
    path('transaction', TransactionViews.as_view()),
]
