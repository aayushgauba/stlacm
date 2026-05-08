from django.test import TestCase
from django.urls import resolve, reverse

from . import views


class StaticHomePageTests(TestCase):
    def test_home_route_resolves_to_home_view(self):
        self.assertEqual(resolve(reverse('home')).func, views.home)

    def test_home_page_returns_200(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_page_core_content_and_seo_tags(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'STL ACM Chapter')
        self.assertContains(response, '<meta name="description"', html=False)
        self.assertContains(response, '<link rel="canonical" href="http://testserver', html=False)
        self.assertContains(response, '<meta property="og:title"', html=False)
        self.assertContains(response, '<meta property="og:description"', html=False)
        self.assertContains(response, '<meta name="twitter:card" content="summary">', html=False)

    def test_removed_routes_return_404(self):
        for route in ['/about/', '/news/', '/venue/', '/speaking/']:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 404)
