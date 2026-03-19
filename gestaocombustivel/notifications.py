# gestaocombustivel/notifications.py - NOVO ARQUIVO

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from gestaocombustivel.models import SeguroViatura


def enviar_alerta_seguro():
    """Envia alerta para seguros a vencer (30 dias)"""
    data_limite = timezone.now().date() + timedelta(days=30)
    seguros = SeguroViatura.objects.filter(
        data_fim__lte=data_limite,
        data_fim__gte=timezone.now().date(),
        ativo=True
    )

    for seguro in seguros:
        dias = (seguro.data_fim - timezone.now().date()).days
        subject = f'ALERTA: Seguro a vencer - {seguro.viatura.matricula}'
        message = f"""
        Seguro da viatura {seguro.viatura.matricula} vence em {dias} dias.
        Apólice: {seguro.numero_apolice}
        Data fim: {seguro.data_fim}
        Companhia: {seguro.companhia_seguros}
        """

        # Enviar para administradores (em produção, pegar emails reais)
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['admin@stae.gov.mz'],
            fail_silently=True
        )


def enviar_notificacao_aprovacao(pedido):
    """Envia notificação quando pedido é aprovado"""
    if pedido.status == 'aprovado' and pedido.solicitante.email:
        subject = f'Pedido de Combustível Aprovado - {pedido.numero_senha}'
        message = f"""
        Seu pedido de combustível foi APROVADO.
        Senha: {pedido.numero_senha}
        Viatura: {pedido.viatura.matricula}
        Quantidade: {pedido.quantidade_litros}L
        Data abastecimento: {pedido.data_abastecimento}
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [pedido.solicitante.email],
            fail_silently=True
        )

# Adicionar no final do save() do PedidoCombustivel
# no models.py, após pedido.save() no método aprovar_pedido_combustivel:
# from .notifications import enviar_notificacao_aprovacao
# enviar_notificacao_aprovacao(pedido)
