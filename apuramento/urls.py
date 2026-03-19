from django.urls import path
from . import views

app_name = 'apuramento'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('lancar/', views.lancar_resultado, name='lancar_resultado'),
    path('editar/<int:resultado_id>/', views.editar_resultado, name='editar_resultado'),
]
