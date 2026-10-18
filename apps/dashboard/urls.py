from django.urls import path

from . import views

app_name = "manage"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("<str:key>/", views.items, name="list"),
    path("<str:key>/ajouter/", views.edit, name="add"),
    path("<str:key>/<int:pk>/modifier/", views.edit, name="edit"),
    path("<str:key>/<int:pk>/basculer/", views.toggle, name="toggle"),
]
