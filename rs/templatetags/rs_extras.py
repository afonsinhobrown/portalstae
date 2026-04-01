from django import template

register = template.Library()

@register.filter
def dict_key(d, key):
    """Retorna o valor de uma chave num dicionário, ou None se não existir ou se d não for dicionário"""
    try:
        return d.get(key)
    except (AttributeError, TypeError):
        return None
