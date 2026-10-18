from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "JEC Sénégal — Administration"
admin.site.site_title = "JEC Sénégal"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("comptes/", include("django.contrib.auth.urls")),
    path("assistant/", include("apps.assistant.urls")),
    path("gestion/", include("apps.dashboard.urls")),
    path("federations/", include("apps.federations.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.content.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
