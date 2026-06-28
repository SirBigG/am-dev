import importlib
import os
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from spirit.category.models import Category
from spirit.comment.models import Comment
from spirit.core.utils.markdown import Markdown
from spirit.topic.models import Topic

from forum_sso.pipeline import create_or_update_forum_user


@override_settings(FORCE_SCRIPT_NAME=None)
class ForumSmokeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="forum-user", password="password")
        self.category = Category.objects.create(title="General", slug="general")
        self.topic = Topic.objects.create(user=self.user, category=self.category, title="Welcome", slug="welcome")
        self.comment = Comment.objects.create(
            user=self.user,
            topic=self.topic,
            comment="Hello forum",
            comment_html="<p>Hello forum</p>",
        )
        self.topic.comment_count = 1
        self.topic.save(update_fields=["comment_count"])

    def forum_path(self, path):
        return path.removeprefix("/forum") or "/"

    def test_forum_home_renders_for_anonymous_user(self):
        response = self.client.get(self.forum_path(reverse("spirit:index")))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spirit/topic/active.html")

    def test_topic_active_list_renders_for_anonymous_user(self):
        response = self.client.get(self.forum_path(reverse("spirit:topic:index-active")))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spirit/topic/active.html")
        self.assertContains(response, self.topic.title)

    def test_category_topic_list_renders_for_anonymous_user(self):
        response = self.client.get(self.forum_path(self.category.get_absolute_url()))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spirit/category/detail.html")
        self.assertContains(response, self.topic.title)

    def test_topic_detail_renders_for_anonymous_user(self):
        response = self.client.get(self.forum_path(self.topic.get_absolute_url()))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spirit/topic/detail.html")
        self.assertContains(response, "Hello forum")

    @override_settings(FORUM_SITE_URL="https://forum.example.com")
    def test_forum_login_routes_to_sso_start(self):
        response = self.client.get("/user/login/", {"next": self.topic.get_absolute_url()})

        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response["Location"])
        self.assertEqual(f"{parsed.scheme}://{parsed.netloc}{parsed.path}", "https://forum.example.com/login/oidc/")

    @override_settings(MAIN_SITE_URL="https://example.com")
    def test_forum_logout_redirects_to_main_site_for_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get("/logout/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://example.com")

    def test_profile_update_renders_for_authenticated_user(self):
        self.client.force_login(self.user)

        response = self.client.get("/user/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "spirit/user/profile_update.html")

    def test_profile_update_requires_authentication(self):
        response = self.client.get("/user/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/sso/start/", response["Location"])


@override_settings(FORCE_SCRIPT_NAME=None)
class ForumSSOViewTests(TestCase):
    @override_settings(FORUM_SITE_URL="https://forum.example.com")
    def test_sso_start_redirects_anonymous_user_to_forum_oidc_begin(self):
        response = self.client.get("/sso/start/", {"next": "/topic/1/"})

        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response["Location"])
        params = parse_qs(parsed.query)
        self.assertEqual(f"{parsed.scheme}://{parsed.netloc}{parsed.path}", "https://forum.example.com/login/oidc/")
        self.assertTrue(params["next"][0].endswith("/topic/1/"))

    @override_settings(FORUM_SITE_URL="https://forum.example.com")
    def test_sso_start_redirects_authenticated_user_to_forum_home(self):
        user = get_user_model().objects.create_user(username="user", password="password")
        self.client.force_login(user)

        response = self.client.get("/sso/start/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://forum.example.com/")

    @override_settings(MAIN_SITE_URL="https://example.com")
    def test_forum_logout_redirects_to_main_site_by_default(self):
        response = self.client.get("/logout/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://example.com")

    @override_settings(MAIN_SITE_URL="https://example.com")
    def test_account_views_redirect_to_main_site_login(self):
        for path in ("/user/register/", "/user/password-reset/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response["Location"], "https://example.com/login/")

    def test_sso_error_returns_forbidden(self):
        response = self.client.get("/sso/error/")

        self.assertEqual(response.status_code, 403)


class ForumMarkdownRenderingTests(TestCase):
    def test_keeps_basic_markdown_and_safe_links(self):
        rendered = Markdown().render("**bold** and [link](https://example.com)")

        self.assertIn("<strong>bold</strong>", rendered)
        self.assertIn('<a rel="nofollow" href="https://example.com">link</a>', rendered)

    def test_escapes_raw_html(self):
        rendered = Markdown().render("<img src=x onerror=alert(1)>")

        self.assertNotIn("<img src=x", rendered)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", rendered)

    def test_strips_javascript_link_protocols(self):
        rendered = Markdown().render("[bad](javascript:alert(1))")

        self.assertNotIn("javascript:", rendered)
        self.assertIn('<a rel="nofollow" href="">bad</a>', rendered)

    def test_strips_javascript_image_protocols(self):
        rendered = Markdown().render("![x](javascript:alert(1))")

        self.assertNotIn("javascript:", rendered)
        self.assertIn('<img src="" alt="x">', rendered)


class FakeStrategy:
    def create_user(self, **fields):
        return get_user_model().objects.create_user(**fields)


class FakeBackend:
    name = "oidc"


class ForumSSOPipelineTests(TestCase):
    def test_ignores_non_oidc_backend(self):
        backend = type("Backend", (), {"name": "google-oauth2"})()

        result = create_or_update_forum_user(FakeStrategy(), {}, backend, uid="123", response={})

        self.assertIsNone(result)

    def test_requires_main_user_identifier(self):
        result = create_or_update_forum_user(FakeStrategy(), {"email": "user@example.com"}, FakeBackend())

        self.assertIsNone(result)

    def test_creates_forum_user_from_oidc_claims(self):
        result = create_or_update_forum_user(
            FakeStrategy(),
            {"email": "jane@example.com"},
            FakeBackend(),
            uid="42",
            response={
                "given_name": "Jane",
                "family_name": "Doe",
                "name": "Jane Doe",
                "is_staff": True,
                "is_superuser": True,
            },
        )

        user = result["user"]
        self.assertFalse(result["is_new"])
        self.assertEqual(user.username, "agromega-42-jane-doe")
        self.assertEqual(user.email, "jane@example.com")
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.st.nickname, "Jane Doe")
        self.assertTrue(user.st.is_administrator)
        self.assertTrue(user.st.is_moderator)

    def test_updates_existing_user_matched_by_email(self):
        user = get_user_model().objects.create_user(
            username="existing",
            email="jane@example.com",
            first_name="Old",
        )

        result = create_or_update_forum_user(
            FakeStrategy(),
            {"email": "JANE@example.com"},
            FakeBackend(),
            uid="42",
            response={"given_name": "Jane", "family_name": "Doe", "name": "Jane Doe"},
        )

        user.refresh_from_db()
        self.assertEqual(result["user"], user)
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Doe")


class ForumStorageSettingsTests(SimpleTestCase):
    def load_forum_storage_settings(self, env):
        import agromega_forum.settings as forum_settings

        with patch.dict(os.environ, env, clear=False):
            forum_settings = importlib.reload(forum_settings)
            result = {
                "media_url": forum_settings.MEDIA_URL,
                "default_storage": forum_settings.STORAGES["default"],
            }
        importlib.reload(forum_settings)
        return result

    def test_s3_storage_normalizes_endpoint_and_builds_bucket_media_url(self):
        settings = self.load_forum_storage_settings(
            {
                "FORUM_STORAGE_BACKEND": "s3",
                "FORUM_AWS_STORAGE_BUCKET_NAME": "forum-bucket",
                "FORUM_AWS_S3_ENDPOINT_URL": "storage.example.com",
                "FORUM_AWS_MEDIA_LOCATION": "forum-media",
                "FORUM_MEDIA_URL": "",
            }
        )

        self.assertEqual(settings["media_url"], "https://forum-bucket.storage.example.com/forum-media/")
        self.assertEqual(settings["default_storage"]["BACKEND"], "storages.backends.s3boto3.S3Boto3Storage")
        self.assertEqual(settings["default_storage"]["OPTIONS"]["endpoint_url"], "https://storage.example.com")
        self.assertEqual(settings["default_storage"]["OPTIONS"]["location"], "forum-media")

    def test_s3_storage_prefers_custom_domain_media_url(self):
        settings = self.load_forum_storage_settings(
            {
                "FORUM_STORAGE_BACKEND": "s3",
                "FORUM_AWS_STORAGE_BUCKET_NAME": "forum-bucket",
                "FORUM_AWS_S3_ENDPOINT_URL": "https://storage.example.com",
                "FORUM_AWS_S3_CUSTOM_DOMAIN": "cdn.example.com",
                "FORUM_AWS_MEDIA_LOCATION": "forum-media",
                "FORUM_MEDIA_URL": "",
            }
        )

        self.assertEqual(settings["media_url"], "https://cdn.example.com/forum-media/")
        self.assertEqual(settings["default_storage"]["OPTIONS"]["endpoint_url"], "https://storage.example.com")
        self.assertEqual(settings["default_storage"]["OPTIONS"]["custom_domain"], "cdn.example.com")
