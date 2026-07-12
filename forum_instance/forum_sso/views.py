from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View
from djconfig import config
from haystack.views import SearchView as BaseSearchView
from spirit.core.utils.paginator import yt_paginate
from spirit.core.utils.views import is_post, post_data, post_files
from spirit.search.forms import AdvancedSearchForm

from .forms import ForumProfileForm
from .urls import forum_url, safe_return_url


class SSOStartView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(forum_url())
        next_url = safe_return_url(request.GET.get("next"))
        # Start the social auth flow on the forum instance itself so the forum
        # stores the `state` value in the user's session. Build the publicly
        # reachable forum begin URL (served under /community on the main nginx host)
        # and include an absolute `next` so the forum knows where to return after auth.
        forum_begin = forum_url("login/oidc/")
        return redirect(f"{forum_begin}?{urlencode({'next': next_url})}")


class ForumLogoutView(View):
    def get(self, request):
        logout(request)
        next_url = safe_return_url(
            request.GET.get("next"),
            default=settings.MAIN_SITE_URL,
            allow_main_site=True,
        )
        return redirect(next_url)


class MainSiteAccountRedirectView(View):
    def get(self, request):
        return redirect(f"{settings.MAIN_SITE_URL}/login/")


class SSOErrorView(View):
    def get(self, request):
        return HttpResponse("Forum sign-in failed. Please return to the main site and try again.", status=403)


class PublicForumSearchView(BaseSearchView):
    def __init__(self, *args, **kwargs):
        super().__init__(
            template="spirit/search/search.html",
            form_class=AdvancedSearchForm,
            load_all=False,
        )

    def build_page(self):
        paginator = None
        from community.models import Publication

        publication_topic_ids = [str(pk) for pk in Publication.objects.values_list("topic_id", flat=True)]
        results = self.results
        if publication_topic_ids:
            # Haystack's django_id is the backing model primary key. Excluding
            # before pagination keeps page sizes and later safe results intact.
            results = results.exclude(django_id__in=publication_topic_ids)
        page = yt_paginate(
            results,
            per_page=config.topics_per_page,
            page_number=self.request.GET.get("page", 1),
        )
        # Keep Spirit's YTPage wrapper intact so render_paginator retains the
        # current page, range, and next/previous navigation metadata.
        page.object_list = [
            {"fields": result.get_stored_fields(), "pk": result.pk}
            for result in page.object_list
        ]
        return paginator, page

    def extra_context(self):
        from django.db.models import Q
        from community.models import Publication

        query = (self.query or "").strip()
        publications = Publication.objects.none()
        if query:
            publications = (
                Publication.objects.published()
                .select_related("author", "topic")
                .prefetch_related("tags")
                .filter(
                    Q(topic__title__icontains=query)
                    | Q(excerpt__icontains=query)
                    | Q(body__icontains=query)
                )
                .distinct()[:10]
            )
        return {"publication_results": publications}


@login_required
def forum_profile_update(request):
    form = ForumProfileForm(
        data=post_data(request),
        files=post_files(request),
        instance=request.user.st,
    )
    if is_post(request) and form.is_valid():
        form.save()
        messages.info(request, _("Your forum profile has been updated!"))
        return redirect(reverse("spirit:user:update"))
    return render_profile_update(request, form)


def render_profile_update(request, form):
    return render(
        request=request,
        template_name="spirit/user/profile_update.html",
        context={"form": form},
    )
