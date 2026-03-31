from accounts.permissions import is_admin


def admin_context(request):
    return {"is_admin_user": is_admin(request.user)}
