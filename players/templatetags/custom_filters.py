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


@register.filter
def ordinal(value):
    """Convert an integer to its ordinal representation (1st, 2nd, 3rd, etc.)"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value

    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')

    return f"{value}{suffix}"
