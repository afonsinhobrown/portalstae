# gestaocombustivel/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve
from .models import Viatura  # ← Import no topo


class ViaturaDisponivelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que requerem verificação
        self.urls_verificar = {
            'pedir_combustivel',
            'solicitar_manutencao',
            # Adicione outros nomes de views aqui
        }

    def __call__(self, request):
        # 1. Identificar a view atual
        try:
            current_view = resolve(request.path_info).view_name
        except:
            current_view = None

        # 2. Verificar apenas nas views específicas
        if current_view in self.urls_verificar and request.method == 'POST':
            viatura_id = request.POST.get('viatura')

            if viatura_id:
                try:
                    viatura = Viatura.objects.get(id=viatura_id)
                    disponivel, motivo = viatura.verificar_disponibilidade()

                    if not disponivel:
                        messages.error(request, f'Viatura não disponível: {motivo}')
                        return redirect('alguma_url_fixa')  # ← URL específica

                except (Viatura.DoesNotExist, ValueError):
                    messages.error(request, 'Viatura inválida')
                    return redirect('alguma_url_fixa')

        return self.get_response(request)