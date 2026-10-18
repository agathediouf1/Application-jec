from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Utilisateur personnalisé. Les droits d'administrateur ne sont jamais donnés automatiquement."""

    class Role(models.TextChoices):
        MEMBER = "member", "Membre"
        SECTION = "section_leader", "Responsable de section"
        FEDERATION = "federation_leader", "Responsable de fédération"
        NATIONAL = "national", "Équipe nationale"

    role = models.CharField("rôle", max_length=20, choices=Role.choices, default=Role.MEMBER)
    federation = models.ForeignKey("federations.Federation", verbose_name="fédération", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="users")
    phone = models.CharField("téléphone", max_length=30, blank=True)

    @property
    def sees_everything(self):
        return self.is_superuser or self.role == self.Role.NATIONAL
