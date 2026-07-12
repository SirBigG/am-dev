from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.html import escape
from django.db.models import Q, Count
from spirit.topic import views as spirit_topic_views
from spirit.topic.models import Topic
from spirit.category.models import Category
from spirit.comment.models import Comment
from spirit.core.utils.paginator import paginate, yt_paginate
from spirit.topic import utils as topic_utils
from djconfig import config

from .forms import EditorImageForm, PublicationForm, ReviewForm
from .models import EditorImage, Publication, PublicationTag
from .services import create_publication, transition, update_publication
from .images import normalize_editor_image


def community_home(request):
    publications = Publication.objects.published().select_related("author", "topic").prefetch_related("tags")[:8]
    publication_topic_ids = Publication.objects.values_list("topic_id", flat=True)
    discussions = (
        Topic.objects.visible()
        .global_()
        .exclude(pk__in=publication_topic_ids)
        .select_related("user", "category")[:8]
    )
    popular_tags = PublicationTag.objects.annotate(publication_count=Count("publications", filter=Q(publications__status=Publication.Status.PUBLISHED))).order_by("-publication_count", "name")[:10]
    return render(request, "community/home.html", {"publications": publications, "discussions": discussions, "popular_tags": popular_tags})


def publication_list(request):
    publications = Publication.objects.published().select_related("author", "topic").prefetch_related("tags")
    query = request.GET.get("q", "").strip()
    tag = request.GET.get("tag", "").strip()
    if query:
        publications = publications.filter(Q(topic__title__icontains=query) | Q(excerpt__icontains=query) | Q(body__icontains=query))
    if tag:
        publications = publications.filter(tags__slug=tag)
    popular_tags = PublicationTag.objects.annotate(publication_count=Count("publications", filter=Q(publications__status=Publication.Status.PUBLISHED))).order_by("-publication_count", "name")[:12]
    publications = publications.distinct()
    return render(request, "community/publication_list.html", {
        "publications": publications,
        "popular_tags": popular_tags,
        "query": query,
        "active_tag": tag,
        "result_count": publications.count(),
    })


def publication_detail(request, slug):
    publication = get_object_or_404(Publication.objects.select_related("author", "topic", "body_comment"), slug=slug)
    can_preview = request.user.is_authenticated and (
        request.user == publication.author or request.user.has_perm("community.review_publication")
    )
    if publication.status != Publication.Status.PUBLISHED and not can_preview:
        raise Http404
    if publication.status == Publication.Status.PUBLISHED:
        # Apply Spirit's public/private/category visibility rules before exposing
        # either the article or its discussion thread.
        Topic.objects.get_public_or_404(publication.topic_id, request.user)
    topic_utils.topic_viewed(request=request, topic=publication.topic)
    comments = (
        Comment.objects.for_topic(topic=publication.topic)
        .exclude(pk=publication.body_comment_id)
        .with_likes(user=request.user)
        .with_polls(user=request.user)
        .order_by("date")
    )
    comments = paginate(
        comments,
        per_page=config.comments_per_page,
        page_number=request.GET.get("page", 1),
    )
    return render(request, "community/publication_detail.html", {
        "publication": publication,
        "topic": publication.topic,
        "comments": comments,
        "reply_count": max(publication.topic.comment_count - 1, 0),
    })


@login_required
def publication_dashboard(request):
    return render(request, "community/publication_dashboard.html", {
        "publications": Publication.objects.filter(author=request.user)
    })


@login_required
def publication_create(request):
    form = PublicationForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy(); values.pop("policy_accept")
        publication = create_publication(user=request.user, **values)
        return redirect(publication)
    return render(request, "community/publication_form.html", {"form": form, "creating": True})


@login_required
def publication_edit(request, slug):
    publication = get_object_or_404(Publication, slug=slug)
    if publication.author != request.user:
        raise PermissionDenied
    form = PublicationForm(request.POST or None, request.FILES or None, instance=publication, initial={"title": publication.topic.title})
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data.copy(); values.pop("policy_accept")
        updated = update_publication(publication, user=request.user, **values)
        return redirect(updated)
    return render(request, "community/publication_form.html", {"form": form, "publication": publication})


@permission_required("community.review_publication", raise_exception=True)
def review_queue(request):
    return render(request, "community/review_queue.html", {
        "publications": Publication.objects.filter(status=Publication.Status.IN_REVIEW)
    })


@require_POST
@login_required
def publication_transition(request, slug, action):
    publication = get_object_or_404(Publication, slug=slug)
    actions = {
        "submit": Publication.Status.IN_REVIEW,
        "publish": Publication.Status.PUBLISHED,
        "request-changes": Publication.Status.CHANGES_REQUESTED,
        "reject": Publication.Status.REJECTED,
        "archive": Publication.Status.ARCHIVED,
    }
    if action not in actions:
        raise Http404
    form = ReviewForm(request.POST)
    if form.is_valid():
        transition(publication, actor=request.user, to_status=actions[action], note=form.cleaned_data["note"])
    return redirect(publication)


def canonical_topic_detail(request, pk, slug=""):
    publication = Publication.objects.filter(topic_id=pk).first()
    if publication:
        if publication.status == Publication.Status.PUBLISHED:
            response = redirect(publication, permanent=True)
            if request.META.get("QUERY_STRING"):
                response["Location"] = f'{response["Location"]}?{request.META["QUERY_STRING"]}'
            return response
        can_preview = request.user.is_authenticated and (
            request.user == publication.author or request.user.has_perm("community.review_publication")
        )
        if not can_preview:
            raise Http404
        return redirect(publication)
    request.is_discussion_page = True
    return spirit_topic_views.detail(request, pk=pk, slug=slug)


def discussion_active(request):
    """Spirit-compatible active list without publication backing topics."""
    publication_topic_ids = Publication.objects.values_list("topic_id", flat=True)
    categories = Category.objects.visible().parents().ordered()
    topics = (
        Topic.objects.visible()
        .global_()
        .exclude(pk__in=publication_topic_ids)
        .with_bookmarks(user=request.user)
        .order_by("-is_globally_pinned", "-last_active")
        .select_related("category", "user")
    )
    topics = yt_paginate(topics, per_page=config.topics_per_page, page_number=request.GET.get("page", 1))
    return render(request, "spirit/topic/active.html", {"categories": categories, "topics": topics})


def discussion_category(request, pk, slug):
    """Spirit-compatible category list without publication backing topics."""
    category = get_object_or_404(Category.objects.visible(), pk=pk)
    if category.slug != slug:
        return redirect(category, permanent=True)
    publication_topic_ids = Publication.objects.values_list("topic_id", flat=True)
    subcategories = Category.objects.visible().children(parent=category).ordered()
    topics = (
        Topic.objects.unremoved()
        .exclude(pk__in=publication_topic_ids)
        .with_bookmarks(user=request.user)
        .for_category(category=category)
        .order_by("-is_globally_pinned", "-is_pinned", "-last_active")
        .select_related("category", "user")
    )
    topics = yt_paginate(topics, per_page=config.topics_per_page, page_number=request.GET.get("page", 1))
    return render(request, "spirit/category/detail.html", {
        "category": category,
        "subcategories": subcategories,
        "topics": topics,
    })


def publication_sitemap(request):
    publications = Publication.objects.published()
    body = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
        f"<url><loc>{escape(request.build_absolute_uri(publication.get_absolute_url()))}</loc>"
        f"<lastmod>{publication.updated_at.date().isoformat()}</lastmod></url>"
        for publication in publications
    ) + "</urlset>"
    return HttpResponse(body, content_type="application/xml")


@require_POST
@login_required
def editor_image_upload(request):
    form = EditorImageForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    image = form.cleaned_data["image"]
    fallback_alt = image.name.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").strip() or "Зображення"
    editor_image = EditorImage.objects.create(
        uploader=request.user, image=normalize_editor_image(image), alt_text=form.cleaned_data.get("alt_text") or fallback_alt
    )
    return JsonResponse({"success": 1, "file": {"url": editor_image.image.url, "alt": editor_image.alt_text}}, status=201)
