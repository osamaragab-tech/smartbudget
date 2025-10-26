# smartbudget/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # accounts app (login, register, logout)
    path('accounts/', include('accounts.urls')),

    # transactions app (dashboard + operations)
    path('', include('transactions.urls')),
]
