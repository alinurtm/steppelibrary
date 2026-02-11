import hashlib
import re

from django import template

register = template.Library()


@register.filter
def status_color(status):
    colors = {
        'available': 'success',
        'reserved': 'warning',
        'on_loan': 'primary',
        'lost': 'danger',
    }
    return colors.get(status, 'secondary')


@register.filter
def open_library_cover(isbn):
    clean_isbn = re.sub(r'[^0-9Xx]', '', str(isbn or ''))
    if len(clean_isbn) not in (10, 13):
        return ''
    return f'https://covers.openlibrary.org/b/isbn/{clean_isbn}-L.jpg?default=false'


@register.filter
def pattern_index(value):
    seed = int(hashlib.md5(str(value).encode('utf-8')).hexdigest(), 16)
    return (seed % 6) + 1


@register.filter
def author_initials(author):
    if hasattr(author, 'first_name') and hasattr(author, 'last_name'):
        first = (author.first_name or '').strip()[:1]
        last = (author.last_name or '').strip()[:1]
        initials = f'{first}{last}'.upper()
        if initials:
            return initials

    parts = str(author).strip().split()
    if not parts:
        return 'AU'
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f'{parts[0][0]}{parts[1][0]}'.upper()


@register.filter
def avatar_hue(author):
    seed = int(hashlib.md5(str(author).encode('utf-8')).hexdigest(), 16)
    return seed % 360
