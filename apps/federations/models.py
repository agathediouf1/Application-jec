from django.db import models
from django.urls import reverse


class Federation(models.Model):
    name = models.CharField("nom", max_length=120)
    slug = models.SlugField(unique=True)
    tagline = models.CharField("slogan", max_length=200, blank=True)
    emblem = models.CharField("sigle", max_length=4, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField("active", default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("federations:detail", args=[self.slug])


class Section(models.Model):
    federation = models.ForeignKey(Federation, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField("nom", max_length=150)
    is_archived = models.BooleanField("archivée", default=False)

    class Meta:
        ordering = ["name"]
        unique_together = [("federation", "name")]

    def __str__(self):
        return f"{self.name} ({self.federation})"


class Leader(models.Model):
    """Coordonnateur ou membre d'équipe. federation vide = Équipe nationale."""

    class Category(models.TextChoices):
        COORD = "coord", "Coordonnateur national"
        TEAM = "team", "Équipe / bureau"

    federation = models.ForeignKey(Federation, null=True, blank=True, on_delete=models.CASCADE, related_name="leaders")
    category = models.CharField("catégorie", max_length=10, choices=Category.choices, default=Category.TEAM)
    full_name = models.CharField("nom complet", max_length=150)
    title = models.CharField("fonction", max_length=200, blank=True)
    order = models.PositiveSmallIntegerField("ordre", default=0)
    is_archived = models.BooleanField("archivé", default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.full_name} — {self.title}" if self.title else self.full_name

    @property
    def initials(self):
        return "".join(w[0] for w in self.full_name.split()[:2]).upper()
