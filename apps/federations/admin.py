from django.contrib import admin

from .models import Federation, Leader, Section


@admin.action(description="Archiver la sélection")
def archive(modeladmin, request, queryset):
    queryset.update(is_archived=True)


@admin.action(description="Restaurer la sélection")
def restore(modeladmin, request, queryset):
    queryset.update(is_archived=False)


class ScopedAdmin(admin.ModelAdmin):
    """Un responsable de fédération ne voit et ne modifie que SA fédération (contrôle côté serveur)."""
    scope_field = "federation"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        u = request.user
        if u.sees_everything:
            return qs
        return qs.filter(**{self.scope_field: u.federation_id}) if u.federation_id else qs.none()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "federation" and not request.user.sees_everything:
            kwargs["queryset"] = Federation.objects.filter(pk=request.user.federation_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0


class LeaderInline(admin.TabularInline):
    model = Leader
    extra = 0


@admin.register(Federation)
class FederationAdmin(ScopedAdmin):
    scope_field = "pk"
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [LeaderInline, SectionInline]

    def has_add_permission(self, request):
        return request.user.sees_everything and super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(request, obj)


@admin.register(Leader)
class LeaderAdmin(ScopedAdmin):
    list_display = ("full_name", "title", "category", "federation", "is_archived")
    list_filter = ("category", "is_archived", "federation")
    search_fields = ("full_name", "title")
    actions = [archive, restore]


@admin.register(Section)
class SectionAdmin(ScopedAdmin):
    list_display = ("name", "federation", "is_archived")
    list_filter = ("is_archived", "federation")
    search_fields = ("name",)
    actions = [archive, restore]
