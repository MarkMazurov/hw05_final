from django.conf import settings
from django.test import TestCase, Client


class CustomPageTest(TestCase):
    """Тестируем кастомные страницы ошибок."""
    def setUp(self):
        self.client = Client()

    def test_404_page(self):
        """Страница 404 отдает кастомный шаблон."""
        if settings.DEBUG is False:
            response = self.client.get('/unexisting_page/')
            self.assertEqual(response.status_code, 404)
            self.assertTemplateUsed(response, 'core/404.html')
