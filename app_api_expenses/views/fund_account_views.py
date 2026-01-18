from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..serializers.currency_serializers import CurrencySerializer, Currency

class CurrencyAPIView(ListAPIView):
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    queryset = Currency.objects.all()