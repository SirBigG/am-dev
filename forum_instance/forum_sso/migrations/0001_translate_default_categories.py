from django.db import migrations


def translate_default_categories(apps, schema_editor):
    Category = apps.get_model("spirit_category", "Category")
    Category.objects.filter(title="Uncategorized", slug="uncategorized", is_private=False).update(
        title="Без категорії",
        slug="bez-kategoriyi",
    )
    Category.objects.filter(title="Private", slug="private", is_private=True).update(
        title="Приватні",
        slug="pryvatni",
    )


def restore_default_categories(apps, schema_editor):
    Category = apps.get_model("spirit_category", "Category")
    Category.objects.filter(title="Без категорії", slug="bez-kategoriyi", is_private=False).update(
        title="Uncategorized",
        slug="uncategorized",
    )
    Category.objects.filter(title="Приватні", slug="pryvatni", is_private=True).update(
        title="Private",
        slug="private",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("spirit_category", "0007_alter_category_id"),
    ]

    operations = [
        migrations.RunPython(translate_default_categories, restore_default_categories),
    ]
