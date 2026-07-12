from django.db import migrations, models


def create_default_tags(apps, schema_editor):
    Tag = apps.get_model("community", "PublicationTag")
    for name, slug, featured in [
        ("Рослинництво", "roslynnytstvo", True), ("Тваринництво", "tvarynnytstvo", True),
        ("Садівництво", "sadivnytstvo", True), ("Овочівництво", "ovochivnytstvo", True),
        ("Техніка", "tekhnika", True), ("Захист рослин", "zakhyst-roslyn", True),
        ("Добрива", "dobryva", False), ("Бізнес", "biznes", False),
        ("Особистий досвід", "osobystyi-dosvid", True), ("Ветеринарія", "veterynariia", False),
    ]:
        Tag.objects.get_or_create(slug=slug, defaults={"name": name, "is_featured": featured})


class Migration(migrations.Migration):
    dependencies = [("community", "0003_direct_publishing_and_editor_images")]
    operations = [
        migrations.CreateModel(name="PublicationTag", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=60, unique=True)),
            ("slug", models.SlugField(allow_unicode=True, max_length=70, unique=True)),
            ("is_featured", models.BooleanField(default=False)),
        ], options={"ordering": ("name",)}),
        migrations.AddField(model_name="publication", name="tags", field=models.ManyToManyField(blank=True, related_name="publications", to="community.publicationtag")),
        migrations.RunPython(create_default_tags, migrations.RunPython.noop),
    ]
