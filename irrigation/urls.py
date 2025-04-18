# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('plot/<int:pk>/', views.PlotDetailView.as_view(), name='plot_detail'),
]