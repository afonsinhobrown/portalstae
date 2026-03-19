# gestaocombustivel/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter(name='split')
def split(value, delimiter=","):
    """
    Filtro split para templates Django
    Uso: {{ minha_string|split:"," }}
    """
    if not value:
        return []
    if isinstance(value, str):
        return value.split(delimiter)
    return []


@register.filter(name='slice_list')
def slice_list(value, slice_str):
    """
    Aplica slice a uma lista
    Uso: {{ minha_lista|slice_list:":3" }}
    """
    if not value or not isinstance(value, list):
        return []

    try:
        # Converte string do slice para índices
        if slice_str.startswith(':'):
            end = int(slice_str[1:]) if slice_str[1:] else None
            return value[:end]
        elif ':' in slice_str:
            parts = slice_str.split(':')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else None
            return value[start:end]
        else:
            return value[:int(slice_str)]
    except:
        return value

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Retorna o valor de um dicionário usando a chave fornecida.
    Uso: {{ meu_dict|get_item:minha_chave }}
    """
    if dictionary and (isinstance(dictionary, dict) or hasattr(dictionary, 'get')):
        # Tenta converter key para string se necessário ou manter como int
        val = dictionary.get(key)
        if val is None:
             val = dictionary.get(str(key))
        return val
    return None

@register.filter(name='filter_by_ponto')
def filter_by_ponto(queryset, ponto_id):
    """
    Filtra uma lista de FuncionarioRota pelo ID do ponto de embarque
    """
    if not queryset:
        return []
    return [item for item in queryset if item.ponto_embarque_id == ponto_id]