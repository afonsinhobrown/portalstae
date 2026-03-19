from django.urls import path
from . import views

app_name = 'eleicoes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
