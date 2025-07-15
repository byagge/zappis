from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
        return [
            'main',
            'demo_dashboard',
            # Добавьте другие имена url, если нужно
        ]

    def location(self, item):
        return reverse(item) 