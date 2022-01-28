from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()
OK = HTTPStatus.OK


class PostURLTests(TestCase):
    """Тестируем URL адреса приложения Post."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.user_2 = User.objects.create_user(username='mark')
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='test_slug',
            description='Описание для теста',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст для тестового поста',
            id=1
        )
        cls.post_2 = Post.objects.create(
            author=cls.user_2,
            text='А это текст второго поста',
            id=2
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_urls_uses_correct_for_guest_clients(self):
        """Доступность страниц для неавторизованных пользователей."""
        url_names = [
            '/',
            '/group/test_slug/',
            '/profile/author/',
            '/posts/1/'
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, OK)

    def test_post_urls_create_and_post_edit(self):
        """Доступность страницы create/ для авторизованного пользователя,
        а также доступность страницы post_edit только для автора поста.
        """
        url_names = [
            '/create/',
            '/posts/1/edit/'
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, OK)

    def test_post_edit_url_redirect_if_not_author(self):
        """Редирект со страницы редактрирования."""
        response = self.authorized_client.get('/posts/2/edit/')
        self.assertRedirects(response, '/posts/2/')

    def test_post_unexisting_page(self):
        """Недоступность несуществующей страницы проекта."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_url_redirect_for_guest_client(self):
        """Редирект неавторизованного пользователя со страницы create/."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_urls_uses_correct_templates(self):
        """URL-адреса используют соответствующие шаблоны."""
        urls_template_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            '/posts/1/edit/': 'posts/post_create.html',
        }
        for address, template in urls_template_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
