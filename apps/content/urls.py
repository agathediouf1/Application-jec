from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("qui-sommes-nous/", views.about, name="about"),
    path("activites/", views.activities, name="activities"),
    path("actualites/", views.news, name="news"),
    path("galerie/", views.gallery, name="gallery"),
    path("documentation/", views.documents, name="documents"),
    path("documentation/<int:pk>/", views.document, name="document"),
    path("glossaire/", views.glossary, name="glossary"),
    path("application/qr.<str:ext>", views.qr_code, name="qr"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="sw"),
    path("hors-ligne/", views.offline, name="offline"),
    path("contact/", views.contact, name="contact"),
]
