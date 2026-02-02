from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< HEAD
    path('', include('app_expenses.urls')),
    path('api/', include('app_api_expenses.urls')),
=======
    path('', include('app_expenses.urls'))
>>>>>>> main
]
