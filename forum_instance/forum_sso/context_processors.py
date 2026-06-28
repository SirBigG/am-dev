from django.conf import settings


def site_links(request):
    main_site_url = settings.MAIN_SITE_URL
    forum_site_url = settings.FORUM_SITE_URL
    return {
        "main_site_url": main_site_url,
        "forum_site_url": forum_site_url,
        "main_login_url": f"{main_site_url}/login/",
        "main_profile_url": f"{main_site_url}/profile/",
        "main_settings_url": f"{main_site_url}/profile/change",
        "main_logout_url": f"{main_site_url}/logout/",
        "main_search_url": f"{main_site_url}/search/",
        "main_news_url": f"{main_site_url}/news/",
        "main_adverts_url": f"{main_site_url}/adverts/",
        "main_events_url": f"{main_site_url}/events/",
        "main_companies_url": f"{main_site_url}/companies/",
        "main_categories_url": f"{main_site_url}/categories/",
    }
