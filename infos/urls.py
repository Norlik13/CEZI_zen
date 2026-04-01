from django.urls import path
from . import views
from . import views_admin

urlpatterns = [
    path("", views.home, name="home"),
    path("articles/", views.articles, name="articles"),

    # UI admin hors /admin/
    path("gestion/pages/", views_admin.page_list, name="page_admin_list"),
    path("gestion/pages/add/", views_admin.page_create, name="page_admin_add"),
    path("gestion/pages/edit/<int:pk>/", views_admin.page_update, name="page_admin_edit"),
    path("gestion/pages/delete/<int:pk>/", views_admin.page_delete, name="page_admin_delete"),

    path("info/<slug:slug>/", views.page_detail, name="page_detail"),
]
