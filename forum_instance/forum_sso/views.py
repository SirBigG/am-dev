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


class SSOStartView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect(f"{settings.FORUM_SITE_URL}/")
        next_url = request.GET.get("next") or f"{settings.FORUM_SITE_URL}/"
        # Start the social auth flow on the forum instance itself so the forum
        # stores the `state` value in the user's session. Build the publicly
        # reachable forum begin URL (served under /forum on the main nginx host)
        # and include an absolute `next` so the forum knows where to return after auth.
        forum_next = next_url if next_url.startswith(("http://", "https://")) else request.build_absolute_uri(next_url)
        forum_begin = f"{settings.FORUM_SITE_URL}/login/oidc/"
        return redirect(f"{forum_begin}?{urlencode({'next': forum_next})}")


class ForumLogoutView(View):
    def get(self, request):
        logout(request)
        next_url = request.GET.get("next") or settings.MAIN_SITE_URL
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
        page = yt_paginate(
            self.results,
            per_page=config.topics_per_page,
            page_number=self.request.GET.get("page", 1),
        )
        page = [{"fields": r.get_stored_fields(), "pk": r.pk} for r in page]
        return paginator, page


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
