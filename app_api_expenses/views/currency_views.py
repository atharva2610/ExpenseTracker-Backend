from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from ..serializers import CurrencySerializer, Currency

class ListCurrencies(ListAPIView):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
