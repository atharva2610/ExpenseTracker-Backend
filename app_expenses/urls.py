from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('', dashboard, name="dashboard"),
    path('fund-accounts/', fund_accounts, name="fund_accounts"),
    path('create-fund-account/', create_fund_account, name="create_fund_account"),
    path('update-fund-account/<uuid:id>/', update_fund_account, name="update_fund_account"),
    path('categories/', categories, name="categories"),
    path('create-category/', create_category, name="create_category"),
    path('update-category/<uuid:id>/', update_category, name="update_category"),
    path('tags/', tags, name="tags"),
    path('create-tag/', create_tag, name="create_tag"),
    path('update-tag/<uuid:id>/', update_tag, name="update_tag"),
    path('transactions/', transactions, name="transactions"),
    path('create-transaction/', create_transaction, name="create_transaction"),
    path('update-transaction/<uuid:id>/', update_transaction, name="update_transaction"),
    path('transaction/fund-account=<fund_acct_id>/', transactions, name="transaction_by_fund_account"),
    path('reports/', report, name="report"),
    path('reports/update/<uuid:id>/', update_report, name="update_report"),
    # path('shortcuts/', shortcuts, name="shortcuts"),
    # path('loans/', loans, name="loans"),
    path('login/', login, name="login"),
    path('logout/', logout, name="logout"),
    path('register/', register, name="register"),
    path('404-not-found/', not_found_404, name="404_not_found"),
    path('no-permission/', no_permission, name="no_permission"),
]