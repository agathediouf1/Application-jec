from django.contrib import admin

from .models import Activity, Article, ContactMessage, Definition, Document, Photo

for m in (Activity, Article, ContactMessage, Definition, Document, Photo):
    admin.site.register(m)
