from http import HTTPStatus

from django.test import TestCase, Client
from django.urls import reverse

OK = HTTPStatus.OK


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_author_and_tech_pages(self):
        """Проверка доступности адресов статичных страниц."""
        url_names = [
            '/about/author/',
            '/about/tech/'
        ]
        for name in url_names:
            with self.subTest(name):
                response = self.guest_client.get(name)
                self.assertEqual(response.status_code, OK)

    def test_static_pages_url_uses_correct_templates(self):
        """Проверка шаблонов для адресов статичных страниц."""
        url_template_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for name, template in url_template_names.items():
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_static_pages_url_accessible_by_name(self):
        """Адреса, генерируемых с помощью имен статичных страниц, доступны."""
        url_views_names = [
            'about:author',
            'about:tech'
        ]
        for name in url_views_names:
            with self.subTest(name=name):
                response = self.guest_client.get(reverse(name))
                self.assertEqual(response.status_code, OK)

    def test_static_pages_uses_correct_templates(self):
        """При обращении к имени статичной страницы
        применяется верный шаблон.
        """
        name_pages_template_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        for name, template in name_pages_template_names.items():
            with self.subTest(name=name):
                response = self.guest_client.get(name)
                self.assertTemplateUsed(response, template)
