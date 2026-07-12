from urllib.parse import urljoin, urlsplit

from django.conf import settings


def forum_url(path=""):
    """Build a public URL without dropping the forum's external path prefix."""
    base = f"{settings.FORUM_SITE_URL.rstrip('/')}/"
    return urljoin(base, path.lstrip("/"))


def safe_return_url(value, *, default=None, allow_main_site=False):
    """Return a trusted public URL for auth/logout redirects."""
    fallback = default or forum_url()
    if not value or value.startswith("//"):
        return fallback

    forum = urlsplit(settings.FORUM_SITE_URL)
    forum_prefix = forum.path.rstrip("/")
    if value.startswith("/"):
        # get_full_path() includes FORCE_SCRIPT_NAME in the proxied application.
        # Avoid joining an already public `/community/...` path onto `/community/` again.
        if forum_prefix and (value == forum_prefix or value.startswith(f"{forum_prefix}/")):
            candidate = f"{forum.scheme}://{forum.netloc}{value}"
        else:
            candidate = forum_url(value)
    else:
        candidate = value
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return fallback

    allowed = {forum.netloc}
    if allow_main_site:
        allowed.add(urlsplit(settings.MAIN_SITE_URL).netloc)
    if parsed.netloc not in allowed:
        return fallback
    required_prefix = f"{forum_prefix}/"
    if not allow_main_site and required_prefix != "/" and not parsed.path.startswith(required_prefix):
        return fallback
    return candidate
