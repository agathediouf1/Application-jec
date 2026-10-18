import apps.content.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("content", "0001_initial")]
    operations = [
        migrations.RenameField("photo", "image", "file"),
        migrations.AlterField("photo", "file", models.FileField(
            upload_to="gallery/", validators=[apps.content.models.safe_file],
            verbose_name="fichier (photo, vidéo, document… tous formats)")),
    ]
