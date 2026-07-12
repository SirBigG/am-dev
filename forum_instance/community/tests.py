from unittest.mock import patch

from djconfig import config
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from spirit.category.models import Category
from spirit.comment.models import Comment
from spirit.topic.models import Topic

from .models import Publication, PublicationTag
from .forms import PublicationForm
from .services import create_publication, transition, update_publication
from .rendering import render_publication_body
from .images import normalize_editor_image


@override_settings(FORCE_SCRIPT_NAME=None)
class PublicationWorkflowTests(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create_user("author", password="pw")
        self.editor = get_user_model().objects.create_user("editor", password="pw")
        self.editor.user_permissions.add(Permission.objects.get(codename="review_publication"))
        Category.objects.create(title="Публікації", slug="publications")
        self.publication = create_publication(
            user=self.author,
            title="Як виростити томати",
            kind=Publication.Kind.GUIDE,
            excerpt="Перевірена практика вирощування.",
            body="Перший абзац.\n\nДругий абзац.",
        )

    def forum_path(self, path):
        return path.removeprefix("/community") or "/"

    def test_create_owns_topic_and_explicit_body_comment(self):
        self.assertEqual(self.publication.topic.user, self.author)
        self.assertEqual(self.publication.body_comment.topic, self.publication.topic)
        self.assertEqual(self.publication.topic.comment_count, 1)
        self.assertNotIn("<script", self.publication.body_html)

    def test_new_publication_is_immediately_public(self):
        response = self.client.get(self.forum_path(self.publication.get_absolute_url()))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.publication.status, Publication.Status.PUBLISHED)
        self.assertIsNotNone(self.publication.policy_accepted_at)

    def test_author_can_preview_and_edit_draft(self):
        self.client.force_login(self.author)
        self.assertEqual(self.client.get(self.forum_path(self.publication.get_absolute_url())).status_code, 200)
        update_publication(
            self.publication, user=self.author, title="Новий заголовок", kind=self.publication.kind,
            excerpt="Оновлений опис", body="Оновлений текст", disclosure=""
        )
        self.publication.refresh_from_db()
        self.assertEqual(self.publication.topic.title, "Новий заголовок")
        self.assertEqual(self.publication.body_comment.comment, "Оновлений текст")

    def test_generic_topic_is_canonical_redirect(self):
        response = self.client.get(self.forum_path(self.publication.topic.get_absolute_url()))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], self.publication.get_absolute_url())
        self.assertContains(self.client.get(self.forum_path(reverse("publications:list"))), self.publication.topic.title)

    def test_generic_topic_redirect_preserves_query_string(self):
        response = self.client.get(
            self.forum_path(self.publication.topic.get_absolute_url()),
            {"from": "notification"},
        )

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], f"{self.publication.get_absolute_url()}?from=notification")

    def test_publication_topic_is_excluded_from_discussion_discovery(self):
        active = self.client.get(self.forum_path(reverse("spirit:topic:index-active")))
        category = self.client.get(self.forum_path(self.publication.topic.category.get_absolute_url()))

        self.assertNotContains(active, self.publication.topic.title)
        self.assertNotContains(category, self.publication.topic.title)

    def test_private_topic_is_not_exposed_on_anonymous_community_home(self):
        private_category = Category.objects.create(
            title="Приватна категорія", slug="private", is_private=True
        )
        private_topic = Topic.objects.create(
            user=self.author,
            category=private_category,
            title="Секретне обговорення",
            slug="secret",
        )
        Comment.objects.create(
            user=self.author,
            topic=private_topic,
            comment="Не показувати",
            comment_html="<p>Не показувати</p>",
        )

        response = self.client.get(self.forum_path(reverse("publications:home")))

        self.assertNotContains(response, private_topic.title)

    def test_publication_detail_renders_replies_with_spirit_compatible_anchor(self):
        reply = Comment.objects.create(
            user=self.editor,
            topic=self.publication.topic,
            comment="Корисне уточнення",
            comment_html="<p>Корисне уточнення</p>",
        )
        self.publication.topic.comment_count = 2
        self.publication.topic.save(update_fields=["comment_count"])

        response = self.client.get(self.forum_path(self.publication.get_absolute_url()))

        self.assertContains(response, "Корисне уточнення")
        self.assertContains(response, 'id="c2"')
        self.assertContains(response, reverse("spirit:comment:find", kwargs={"pk": reply.pk}))
        self.assertNotContains(response, '>Додати коментар</a>')

    def test_publication_comment_pagination_excludes_hidden_body_comment(self):
        replies = []
        for number in range(3):
            replies.append(Comment.objects.create(
                user=self.editor,
                topic=self.publication.topic,
                comment=f"Відповідь {number + 1}",
                comment_html=f"<p>Відповідь {number + 1}</p>",
            ))
        self.publication.topic.comment_count = 4
        self.publication.topic.save(update_fields=["comment_count"])

        with patch.dict(config._cache, {"comments_per_page": 2}):
            response = self.client.get(
                self.forum_path(self.publication.get_absolute_url()),
                {"page": 2},
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, replies[-1].comment)
        self.assertNotContains(response, self.publication.body_comment.comment)
        self.assertEqual(list(response.context["comments"].object_list), [replies[-1]])

    def test_publication_compose_uses_only_its_dedicated_header(self):
        self.client.force_login(self.author)

        response = self.client.get(self.forum_path(reverse("publications:create")))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="medium-compose__actions"')
        self.assertNotContains(response, 'class="medium-compose__bar"')
        self.assertNotContains(response, 'class="community-tabs"')
        self.assertNotContains(response, 'class="community-mobile-nav"')

    def test_publication_form_allows_empty_release_taxonomy_and_exposes_kind(self):
        PublicationTag.objects.all().delete()
        form = PublicationForm(data={
            "title": "Досвід вирощування",
            "kind": Publication.Kind.EXPERIENCE,
            "excerpt": "Практичний опис досвіду.",
            "body": "Корисний текст публікації.",
            "disclosure": "",
            "policy_accept": "on",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["kind"], Publication.Kind.EXPERIENCE)

    def test_publication_is_present_in_list_and_sitemap(self):
        self.assertContains(self.client.get(self.forum_path(reverse("publications:list"))), self.publication.topic.title)
        self.assertContains(self.client.get(self.forum_path(reverse("publications:sitemap"))), self.publication.get_absolute_url())

    def test_public_pages_have_single_main_landmark_and_heading(self):
        for url in (
            reverse("publications:home"),
            reverse("publications:list"),
            self.publication.get_absolute_url(),
            reverse("spirit:topic:index-active"),
        ):
            response = self.client.get(self.forum_path(url))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.count(b"<main"), 1)
            self.assertEqual(response.content.count(b"<h1"), 1)

    def test_unsafe_transition_is_rejected(self):
        with self.assertRaisesMessage(Exception, "Цей перехід"):
            transition(self.publication, actor=self.editor, to_status=Publication.Status.PUBLISHED)

    def test_structured_editor_blocks_are_rendered_with_an_allowlist(self):
        html = str(render_publication_body("## Розділ\n\n> Порада\n\n- Один\n- Два\n\n---\n\n![Поле](https://example.com/field.jpg)\n<script>alert(1)</script>"))
        self.assertIn("<h2>Розділ</h2>", html)
        self.assertIn("<blockquote>Порада</blockquote>", html)
        self.assertIn("<ul><li>Один</li><li>Два</li></ul>", html)
        self.assertIn("<figure>", html)
        self.assertNotIn("<script>", html)

    def test_authenticated_author_can_upload_editor_image(self):
        self.client.force_login(self.author)
        gif = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        response = self.client.post(self.forum_path(reverse("publications:editor-image-upload")), {
            "image": SimpleUploadedFile("field.gif", gif, content_type="image/gif"), "alt_text": "Поле"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("/media/community/editor/", response.json()["file"]["url"])

    def test_editorjs_upload_does_not_require_caption_before_preview(self):
        self.client.force_login(self.author)
        gif = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        response = self.client.post(self.forum_path(reverse("publications:editor-image-upload")), {
            "image": SimpleUploadedFile("tomato-field.gif", gif, content_type="image/gif")
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["success"], 1)
        self.assertTrue(response.json()["file"]["url"].endswith(".webp"))

    def test_editorjs_json_is_rendered_from_allowlisted_blocks(self):
        html = str(render_publication_body('{"blocks":[{"type":"header","data":{"text":"Врожай","level":2}},{"type":"paragraph","data":{"text":"<script>bad</script>Порада"}},{"type":"delimiter","data":{}}]}'))
        self.assertIn("<h2>Врожай</h2>", html)
        self.assertIn("Порада", html)
        self.assertNotIn("<script>", html)
