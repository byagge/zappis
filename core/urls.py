from django.conf import settings
from django.urls import include, path
from django.contrib import admin

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from apps.search import views as search_views

from django.contrib.sitemaps.views import sitemap
from apps.main.sitemaps import StaticViewSitemap
from apps.main import views as main_views

sitemaps = {
    'static': StaticViewSitemap,
}

handler404 = main_views.custom_404
handler500 = main_views.custom_500
handler403 = main_views.custom_403
handler400 = main_views.custom_400
handler405 = main_views.custom_405

urlpatterns = [
    path("django-admin/", admin.site.urls),  # Unfold/Django admin
    path("admin/", include(wagtailadmin_urls)),  # Wagtail admin
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    path("accounts/", include("apps.accounts.urls")),
    path("businesses/", include("apps.businesses.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("employees/", include("apps.employees.urls")),
    path("schedules/", include("apps.schedules.urls")),
    path("services/", include("apps.services.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("settings/", include("apps.settings.urls")),
    path("clients/", include("apps.clients.urls")),
    path("o/", include("apps.website.urls")),  # Новый сайт
    path("employee/", include("apps.employee.urls")),
    path("support/", include("apps.help.urls")),
    path("", include("apps.main.urls")),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django_sitemap'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Wagtail page serving — только в самом конце!
urlpatterns += [
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
