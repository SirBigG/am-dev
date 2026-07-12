from django.urls import path

from . import views

app_name = "publications"

urlpatterns = [
    path("", views.community_home, name="home"),
    # These owned views intentionally precede Spirit and remove publication
    # backing topics from discussion discovery while retaining Spirit URLs.
    path("topic/active/", views.discussion_active, name="discussion-active"),
    path("category/<int:pk>/<str:slug>/", views.discussion_category, name="discussion-category"),
    path("publications/", views.publication_list, name="list"),
    path("publications/new/", views.publication_create, name="create"),
    path("publications/mine/", views.publication_dashboard, name="dashboard"),
    path("publications/review/", views.review_queue, name="review-queue"),
    path("publications/editor/image-upload/", views.editor_image_upload, name="editor-image-upload"),
    path("publications/<str:slug>/", views.publication_detail, name="detail"),
    path("publications/<str:slug>/edit/", views.publication_edit, name="edit"),
    path("publications/<str:slug>/<str:action>/", views.publication_transition, name="transition"),
    path("sitemap.xml", views.publication_sitemap, name="sitemap"),
    path("topic/<int:pk>/<str:slug>/", views.canonical_topic_detail, name="topic-canonical"),
    path("topic/<int:pk>/", views.canonical_topic_detail, kwargs={"slug": ""}),
]
