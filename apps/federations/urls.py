from django.urls import path

from . import views

app_name = "federations"
urlpatterns = [
    path("", views.federation_list, name="list"),
    path("equipe-nationale/", views.national_team, name="national"),
    path("<slug:slug>/", views.federation_detail, name="detail"),
]
