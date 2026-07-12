from django import forms

from .models import Publication, PublicationTag


class PublicationForm(forms.ModelForm):
    title = forms.CharField(max_length=255, label="Заголовок", widget=forms.TextInput(attrs={"class": "medium-title-input", "placeholder": "Заголовок матеріалу"}))
    policy_accept = forms.BooleanField(
        label="Я приймаю правила публікації",
        help_text="Ви відповідаєте за достовірність, законність і права на матеріал. AgroMega може приховати або видалити контент, що порушує правила чи закон.",
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=PublicationTag.objects.all(), required=False, label="Теми",
        widget=forms.CheckboxSelectMultiple,
        help_text="Оберіть до п’яти тем, за якими читачі знайдуть матеріал.",
    )

    class Meta:
        model = Publication
        fields = ("title", "kind", "excerpt", "body", "tags", "disclosure")
        labels = {
            "kind": "Тип публікації",
            "excerpt": "Короткий опис",
            "disclosure": "Розкриття співпраці",
        }
        widgets = {
            "body": forms.Textarea(attrs={"rows": 22, "class": "medium-editor__input", "data-medium-editor": "body", "placeholder": "Розкажіть свою історію…"}),
            "excerpt": forms.Textarea(attrs={"rows": 3, "class": "medium-summary-input", "placeholder": "Коротко поясніть, чим матеріал буде корисний"}),
        }

    def clean_tags(self):
        tags = self.cleaned_data["tags"]
        if tags.count() > 5:
            raise forms.ValidationError("Можна обрати не більше п’яти тем.")
        return tags


class ReviewForm(forms.Form):
    note = forms.CharField(required=False, label="Нотатка редактора", widget=forms.Textarea(attrs={"rows": 4}))


class EditorImageForm(forms.Form):
    image = forms.ImageField()
    alt_text = forms.CharField(max_length=240, required=False)

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image.size > 8 * 1024 * 1024:
            raise forms.ValidationError("Зображення має бути меншим за 8 МБ.")
        if image.content_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
            raise forms.ValidationError("Підтримуються JPEG, PNG, WebP та GIF.")
        return image
