from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from spirit.category.models import Category
from spirit.comment.models import Comment
from spirit.topic.models import Topic

from .models import Publication, PublicationStatusEvent
from .rendering import render_publication_body

TRANSITIONS = {
    Publication.Status.DRAFT: {Publication.Status.IN_REVIEW},
    Publication.Status.CHANGES_REQUESTED: {Publication.Status.DRAFT, Publication.Status.IN_REVIEW},
    Publication.Status.IN_REVIEW: {Publication.Status.PUBLISHED, Publication.Status.CHANGES_REQUESTED, Publication.Status.REJECTED},
    Publication.Status.PUBLISHED: {Publication.Status.IN_REVIEW, Publication.Status.ARCHIVED},
}


def _unique_slug(title):
    base = slugify(title, allow_unicode=True)[:160] or "publication"
    candidate, suffix = base, 2
    while Publication.objects.filter(slug=candidate).exists():
        candidate = f"{base[:170-len(str(suffix))]}-{suffix}"
        suffix += 1
    return candidate


def _publication_category():
    category = Category.objects.filter(is_removed=False, is_private=False).order_by("pk").first()
    if not category:
        raise ValidationError("Спочатку створіть публічну категорію форуму.")
    return category


@transaction.atomic
def create_publication(*, user, title, excerpt, body, tags=None, kind=None, disclosure=""):
    topic = Topic.objects.create(user=user, category=_publication_category(), title=title)
    html = str(render_publication_body(body))
    comment = Comment.objects.create(user=user, topic=topic, comment=body, comment_html=html)
    topic.increase_comment_count()
    topic.refresh_from_db(fields=("comment_count",))
    now = timezone.now()
    publication = Publication.objects.create(
        topic=topic, body_comment=comment, author=user, slug=_unique_slug(title),
        excerpt=excerpt, body=body, body_html=html, disclosure=disclosure,
        status=Publication.Status.PUBLISHED, published_at=now, policy_accepted_at=now,
    )
    publication.tags.set(tags or ())
    return publication


@transaction.atomic
def update_publication(publication, *, user, **values):
    if user != publication.author or publication.status == Publication.Status.ARCHIVED:
        raise PermissionDenied
    publication.topic.title = values.pop("title")
    tags = values.pop("tags", publication.tags.all())
    publication.topic.save(update_fields=("title", "slug", "reindex_at"))
    for name, value in values.items():
        setattr(publication, name, value)
    publication.body_html = str(render_publication_body(publication.body))
    publication.body_comment.comment = publication.body
    publication.body_comment.comment_html = publication.body_html
    publication.body_comment.save(update_fields=("comment", "comment_html", "modified_count"))
    publication.status = Publication.Status.PUBLISHED
    publication.published_at = publication.published_at or timezone.now()
    publication.policy_accepted_at = timezone.now()
    publication.full_clean()
    publication.save()
    publication.tags.set(tags)
    return publication


@transaction.atomic
def transition(publication, *, actor, to_status, note=""):
    if to_status not in TRANSITIONS.get(publication.status, set()):
        raise ValidationError("Цей перехід стану не дозволено.")
    editing = actor == publication.author and to_status in {Publication.Status.DRAFT, Publication.Status.IN_REVIEW}
    reviewing = actor.has_perm("community.review_publication")
    if not (editing or reviewing):
        raise PermissionDenied
    previous = publication.status
    publication.status = to_status
    now = timezone.now()
    if to_status == Publication.Status.IN_REVIEW:
        publication.submitted_at = now
    if to_status == Publication.Status.PUBLISHED:
        publication.published_at = now
    publication.save()
    PublicationStatusEvent.objects.create(
        publication=publication, actor=actor, from_status=previous, to_status=to_status, note=note
    )
    return publication
