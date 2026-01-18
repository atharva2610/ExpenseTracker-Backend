from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views.auth_views import *
from .views.fund_account_views import *

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh_api'), # returns refresh Token
    path('login/', LoginAPIView.as_view(), name='login_api'),
    path('user/', UserAPIView.as_view(), name='user_api'),
    path('list-fund-accounts/', CurrencyAPIView.as_view(), name='currency_api'),
]