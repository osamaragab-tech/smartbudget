# accounts/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import register_view, CustomLoginView

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
