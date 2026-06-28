from django.contrib.auth import get_user_model
from django.utils.text import slugify


def create_or_update_forum_user(strategy, details, backend, uid=None, user=None, response=None, *args, **kwargs):
    if backend.name != "oidc":
        return None

    claims = response or {}
    main_user_id = str(uid or claims.get("sub") or "")
    if not main_user_id:
        return None

    email = (details.get("email") or claims.get("email") or "").strip()
    first_name = (details.get("first_name") or claims.get("given_name") or "").strip()
    last_name = (details.get("last_name") or claims.get("family_name") or "").strip()
    display_name = (details.get("fullname") or claims.get("name") or f"{first_name} {last_name}").strip()
    username = _build_username(main_user_id, display_name, email)

    if user is None:
        user = _find_existing_user(username, email)
        if user is None:
            user = strategy.create_user(username=username, email=email)

    changed = False
    for field, value in {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
    }.items():
        if value and hasattr(user, field) and getattr(user, field) != value:
            setattr(user, field, value)
            changed = True
    if changed:
        user.save()

    is_forum_admin = bool(claims.get("is_superuser") or claims.get("is_staff"))
    profile = getattr(user, "st", None)
    if profile is not None:
        profile_changed = False
        if display_name and _should_initialize_nickname(profile.nickname, user.username, main_user_id):
            profile.nickname = display_name
            slug = slugify(display_name, allow_unicode=True)
            if slug:
                profile.slug = slug
            profile_changed = True
        if profile.is_administrator != is_forum_admin:
            profile.is_administrator = is_forum_admin
            profile_changed = True
        if profile.is_moderator != is_forum_admin:
            profile.is_moderator = is_forum_admin
            profile_changed = True
        if profile_changed:
            profile.save()

    auth_changed = False
    if user.is_staff != is_forum_admin:
        user.is_staff = is_forum_admin
        auth_changed = True
    if user.is_superuser != bool(claims.get("is_superuser")):
        user.is_superuser = bool(claims.get("is_superuser"))
        auth_changed = True
    if auth_changed:
        user.save(update_fields=["is_staff", "is_superuser"])

    return {"user": user, "is_new": False}


def _find_existing_user(username, email):
    User = get_user_model()
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        pass

    if email:
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
    return None


def _build_username(main_user_id, display_name, email):
    source = display_name or email.split("@", 1)[0] or "user"
    slug = slugify(source, allow_unicode=False) or "user"
    return f"agromega-{main_user_id}-{slug}"[:150]


def _should_initialize_nickname(nickname, username, main_user_id):
    if not nickname:
        return True
    if nickname == username:
        return True
    return nickname.startswith(f"agromega-{main_user_id}-")
