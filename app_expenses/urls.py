from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name="dashboard"),
    path('transactions/', transactions, name="transactions"),
    path('fund_accounts/', fund_accounts, name="fund_accounts"),
    path('categories/', categories, name="categories"),
    path('tags/', tags, name="tags"),
    path('shortcuts/', shortcuts, name="shortcuts"),
    path('reports/', reports, name="reports"),
    path('loans/', loans, name="loans"),
    path('login/', login, name="login"),
    path('logout/', logout, name="logout"),
    path('register/', register, name="register"),
    path('404-not-found/', not_found_404, name="404_not_found"),
    path('no-permission/', no_permission, name="no_permission"),
]
