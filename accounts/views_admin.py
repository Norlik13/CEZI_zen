from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UserAdminForm
from .models import User
from .permissions import is_admin


@user_passes_test(is_admin)
def user_list(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.all().order_by("-date_joined")

    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))

    return render(
        request,
        "accounts/admin/user_list.html",
        {"users": users, "query": query},
    )


@user_passes_test(is_admin)
def user_edit(request, pk):
    target = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserAdminForm(request.POST, instance=target)
        if form.is_valid():
            updated_user = form.save(commit=False)

            # Prevent locking yourself out from admin UI.
            if request.user.pk == target.pk:
                removing_own_staff = request.user.is_staff and not updated_user.is_staff
                if not updated_user.is_active or removing_own_staff:
                    form.add_error(
                        None,
                        "Vous ne pouvez pas retirer vos propres droits admin staff ou desactiver votre compte.",
                    )
            if not form.errors:
                updated_user.save()
                form.save_m2m()
                messages.success(request, "Utilisateur mis a jour.")
                return redirect("user_admin_list")
    else:
        form = UserAdminForm(instance=target)

    return render(
        request,
        "accounts/admin/user_form.html",
        {"form": form, "target": target},
    )
