import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("community", "0002_alter_publication_slug"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.RemoveField(model_name="publication", name="cover"),
        migrations.RemoveField(model_name="publication", name="cover_alt"),
        migrations.AddField(model_name="publication", name="policy_accepted_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="publication", name="policy_version", field=models.CharField(default="2026-07-11", max_length=20)),
        migrations.CreateModel(
            name="EditorImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="community/editor/%Y/%m/")),
                ("alt_text", models.CharField(max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("uploader", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="community_images", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
