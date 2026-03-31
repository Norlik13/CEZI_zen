from django import template

from accounts.permissions import is_admin

register = template.Library()


@register.filter
def is_admin_user(user):
    return is_admin(user)
