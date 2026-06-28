from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from forum_sso import views as sso_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sso/start/", sso_views.SSOStartView.as_view(), name="sso-start"),
    path("sso/error/", sso_views.SSOErrorView.as_view(), name="sso-error"),
    path("logout/", sso_views.ForumLogoutView.as_view(), name="forum-logout"),
    path("search/", sso_views.PublicForumSearchView(), name="forum-search"),
    path("user/", sso_views.forum_profile_update, name="forum-profile-update"),
    path("user/login/", sso_views.SSOStartView.as_view(), name="forum-login"),
    path("user/register/", sso_views.MainSiteAccountRedirectView.as_view(), name="forum-register"),
    path("user/password-reset/", sso_views.MainSiteAccountRedirectView.as_view(), name="forum-password-reset"),
    path("", include("social_django.urls", namespace="social")),
    path("", include("spirit.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
