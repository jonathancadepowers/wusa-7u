from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def multiply(value, arg):
    """Multiply the value by the arg"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0
