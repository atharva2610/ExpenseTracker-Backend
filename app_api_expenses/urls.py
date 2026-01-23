from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh_api'), # returns refresh Token
    path('login/', LoginAPIView.as_view(), name='login_api'),
    path('user/', UserAPIView.as_view(), name='user_api'),
    path('currencies/', ListCurrencies.as_view(), name='currency_list_api'),
    path('fund-accounts/', ListFundAccounts.as_view(), name='list_fund_accounts_api'),
    path('fund-account/create/', CreateFundAccount.as_view(), name='create_fund_account_api'),
    path('fund-account/<int:pk>/', RetrieveFundAccount.as_view(), name='retrieve_fund_account_api'),
]