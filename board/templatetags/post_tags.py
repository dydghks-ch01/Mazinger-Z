# board/templatetags/post_tags.py

from django import template
from board.models import PostScrap

register = template.Library()

@register.filter
def scrapped(post, user):
    if user.is_authenticated:
        return PostScrap.objects.filter(post=post, user=user).exists()
    return False
