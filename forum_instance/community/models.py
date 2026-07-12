from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class PublicationQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=Publication.Status.PUBLISHED, topic__is_removed=False)


class PublicationTag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, allow_unicode=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Publication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        IN_REVIEW = "in_review", "На розгляді"
        CHANGES_REQUESTED = "changes_requested", "Потрібні зміни"
        PUBLISHED = "published", "Опубліковано"
        REJECTED = "rejected", "Відхилено"
        ARCHIVED = "archived", "В архіві"

    class Kind(models.TextChoices):
        GUIDE = "guide", "Практичний посібник"
        RANKING = "ranking", "Добірка або рейтинг"
        EXPERT = "expert", "Експертний матеріал"
        EXPERIENCE = "experience", "Особистий досвід"
        EDITORIAL = "editorial", "Матеріал редакції"

    topic = models.OneToOneField("spirit_topic.Topic", on_delete=models.PROTECT, related_name="publication")
    body_comment = models.OneToOneField(
        "spirit_comment.Comment", on_delete=models.PROTECT, related_name="publication_body"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="publications")
    slug = models.SlugField(max_length=180, unique=True, allow_unicode=True)
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.EXPERIENCE)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.DRAFT, db_index=True)
    excerpt = models.TextField(max_length=500)
    body = models.TextField()
    body_html = models.TextField(editable=False)
    editorial_notes = models.TextField(blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)
    is_editorial = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    disclosure = models.CharField(max_length=240, blank=True)
    tags = models.ManyToManyField(PublicationTag, related_name="publications", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    policy_version = models.CharField(max_length=20, default="2026-07-11")
    policy_accepted_at = models.DateTimeField(null=True, blank=True)

    objects = PublicationQuerySet.as_manager()

    class Meta:
        ordering = ("-published_at", "-created_at")
        permissions = (("review_publication", "Can review and publish community publications"),)

    def clean(self):
        if self.topic_id and self.author_id != self.topic.user_id:
            raise ValidationError("Автор публікації має збігатися з автором теми.")
        if self.body_comment_id and self.topic_id and self.body_comment.topic_id != self.topic_id:
            raise ValidationError("Основний коментар має належати темі публікації.")

    def get_absolute_url(self):
        return reverse("publications:detail", kwargs={"slug": self.slug})


class PublicationStatusEvent(models.Model):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE, related_name="status_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    from_status = models.CharField(max_length=24, choices=Publication.Status.choices)
    to_status = models.CharField(max_length=24, choices=Publication.Status.choices)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)


class EditorImage(models.Model):
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="community_images")
    image = models.ImageField(upload_to="community/editor/%Y/%m/")
    alt_text = models.CharField(max_length=240)
    created_at = models.DateTimeField(auto_now_add=True)
