from django.urls import path
from . import views


urlpatterns = [
    path('search_view', views.home, name='search_view'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    
]