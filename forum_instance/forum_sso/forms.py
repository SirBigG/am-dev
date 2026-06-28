from django import forms
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from spirit.user.forms import UserProfileForm as SpiritUserProfileForm


class ForumProfileForm(SpiritUserProfileForm):
    nickname = forms.CharField(label="Публічне ім'я на форумі", max_length=255)

    class Meta(SpiritUserProfileForm.Meta):
        fields = ("nickname", "avatar", "location", "timezone")

    def clean_nickname(self):
        nickname = self.cleaned_data["nickname"].strip()
        if not nickname:
            raise forms.ValidationError(_("This field is required."))
        return nickname

    def save(self, *args, **kwargs):
        self.instance.nickname = self.cleaned_data["nickname"]
        slug = slugify(self.cleaned_data["nickname"], allow_unicode=True)
        if slug:
            self.instance.slug = slug
        return super().save(*args, **kwargs)
