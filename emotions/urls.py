from django.urls import path
from . import views, views_admin
from . import views_admin

# User URLs
urlpatterns = [
    path("", views.tracker_list, name="tracker_list"),
    path("add/", views.tracker_create, name="tracker_add"),
    path("edit/<int:pk>/", views.tracker_update, name="tracker_edit"),
    path("delete/<int:pk>/", views.tracker_delete, name="tracker_delete"),
    path("report/", views.tracker_report, name="tracker_report"),
]

# Admin URLs
urlpatterns += [
    path("ref/base/", views_admin.base_list, name="base_list"),
    path("ref/base/add/", views_admin.base_create, name="base_add"),
    path("ref/base/edit/<int:pk>/", views_admin.base_update, name="base_edit"),
    path("ref/base/delete/<int:pk>/", views_admin.base_delete, name="base_delete"),

    path("ref/emotion/", views_admin.emotion_list, name="emotion_list"),
    path("ref/emotion/add/", views_admin.emotion_create, name="emotion_add"),
    path("ref/emotion/edit/<int:pk>/", views_admin.emotion_update, name="emotion_edit"),
    path("ref/emotion/delete/<int:pk>/", views_admin.emotion_delete, name="emotion_delete"),
]
