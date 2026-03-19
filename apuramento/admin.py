from django.contrib import admin
from .models import ResultadoMesa

@admin.register(ResultadoMesa)
class ResultadoMesaAdmin(admin.ModelAdmin):
    list_display = ['mesa', 'posto', 'partido', 'votos_validos', 'data_apuramento']
    list_filter = ['posto', 'partido']
