from rest_framework import serializers
from app_expenses.models import Currency

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'