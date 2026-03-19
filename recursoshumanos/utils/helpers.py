# recursoshumanos/utils/helpers.py

from django.db.models import Count, Sum, Q
from recursoshumanos.models import Funcionario, RegistroPresenca, Licenca

def get_funcionario_or_none(user):
    """
    Retorna o Funcionario associado ao user, ou None se não existir.
    Útil para admins que não têm registro de funcionário.
    """
    try:
        return Funcionario.objects.get(user=user)
    except Funcionario.DoesNotExist:
        return None


def get_funcionario_or_admin_view(user):
    """
    Para views que precisam de Funcionario:
    - Se user tem Funcionario: retorna o funcionario
    - Se user é admin/staff: retorna None (permitindo acesso total)
    - Caso contrário: levanta exceção
    """
    try:
        return Funcionario.objects.get(user=user)
    except Funcionario.DoesNotExist:
        if user.is_staff or user.is_superuser:
            return None  # Admin pode ver tudo
        raise Funcionario.DoesNotExist("Você precisa de um perfil de funcionário para acessar esta página.")


from datetime import date, timedelta

def calcular_dias_uteis(data_inicio, data_fim):
    """
    Calcula dias úteis (exclui fins de semana)
    """
    dias = 0
    current_date = data_inicio

    while current_date <= data_fim:
        if current_date.weekday() < 5:  # 0-4 = segunda a sexta
            dias += 1
        current_date += timedelta(days=1)

    return dias


def gerar_relatorio_presencas_mensal(mes, ano):
    """
    Gera relatório de presenças para o mês
    Retorna dados para integração com outras apps
    """
    data_inicio = date(ano, mes, 1)
    if mes == 12:
        data_fim = date(ano + 1, 1, 1) - timedelta(days=1)
    else:
        data_fim = date(ano, mes + 1, 1) - timedelta(days=1)

    presencas = RegistroPresenca.objects.filter(
        data_hora__date__gte=data_inicio,
        data_hora__date__lte=data_fim
    ).values('funcionario').annotate(
        dias_presentes=Count('id', filter=Q(tipo='entrada')),
        total_horas=Sum('horas_trabalhadas')
    )

    return list(presencas)


def verificar_conflito_ferias(funcionario_id, data_inicio, data_fim):
    """
    Verifica se há conflito com outras férias ou licenças
    """
    conflitos = Licenca.objects.filter(
        funcionario_id=funcionario_id,
        status='aprovado',
        data_inicio__lte=data_fim,
        data_fim__gte=data_inicio
    ).exists()

    return conflitos
