import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, Follow

User = get_user_model()

url_names = [
    reverse('posts:index'),
    reverse(
        'posts:group_list',
        kwargs={'slug': 'test_slug'}),
    reverse(
        'posts:profile',
        kwargs={'username': 'author'}),
]

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BaseTest(TestCase):
    """Базовый класс для тестов:
    определяем setUpClass() и setUp().
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='test.gif',
            content=test_image,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Группа',
            slug='test_slug',
            description='Описание для теста'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
            group=cls.group,
            image=cls.image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)


class PostPagesTest(BaseTest):
    """Тестируем отображения приложения Post."""
    def test_post_pages_uses_correct_templates(self):
        """URL-адреса приложения Post используют
        соответствующие шаблоны.
        """
        pages_templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'author'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for name, template in pages_templates_names.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с верным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': '1'})))
        self.assertEqual(response.context.get(
            'post').author, self.user)
        self.assertEqual(response.context.get(
            'post').text, self.post.text)
        self.assertEqual(response.context.get('post').id, 1)
        self.assertEqual(response.context.get(
            'post').group, self.group)
        self.assertEqual(response.context.get(
            'post').image.name,
            f'posts/{self.image.name}'
        )

    def test_post_pages_with_posts_show_correct_context(self):
        """Шаблоны index, group_list и profile
        сформированы с верным контекстом.
        """
        for name in url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                first_post = response.context['page_obj'][0]
                post_author_0 = first_post.author
                post_text_0 = first_post.text
                post_id_0 = first_post.id
                post_group_0 = first_post.group
                post_image_0 = first_post.image.name
                self.assertEqual(post_author_0, self.user)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_id_0, 1)
                self.assertEqual(post_group_0, self.group)
                self.assertEqual(post_image_0, f'posts/{self.image.name}')

    def test_post_pages_with_form_show_correct_context(self):
        """Шаблоны post_create и post_edit сформированы с верным контекстом."""
        urls_create_edit = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}),
        ]
        for name in urls_create_edit:
            response = self.authorized_client.get(name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField
            }
            for value, expected in form_fields.items():
                with self.subTest(name=name, value=value):
                    form_field = response.context.get(
                        'form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_index_page_cache_work_correct(self):
        """Кэширование главной страницы работает правильно."""
        guest = Client()
        post_count_1 = Post.objects.count()
        cache_1 = guest.get(reverse('posts:index')).content
        self.post.delete()
        cache_2 = guest.get(reverse('posts:index')).content
        self.assertEqual(cache_1, cache_2)
        cache.clear()
        self.assertEqual(Post.objects.count(), post_count_1 - 1)


def post_contains_func(self, page, index):
    """Функция проверки соответствия содержания постов
    на страницах index, group_list и profile с ожиданиями."""
    post_author = page[index].author
    post_text = page[index].text
    post_group = page[index].group
    self.assertEqual(post_author, self.user)
    self.assertEqual(post_text, self.post[0].text)
    self.assertEqual(post_group, self.group)


class PaginatorViewsTest(BaseTest):
    """Тестируем паджинатор."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.bulk_create([
            Post(
                author=cls.user,
                text='Текст поста',
                group=cls.group,
            ) for i in range(12)
        ])

    def test_first_page_contains_ten_posts(self):
        """На первой странице должно быть 10 записей,
        а на второй странице - только 3 записи.
        """
        for name in url_names:
            with self.subTest(name=name):

                """Здесь тестируем первую страницу."""
                response = self.authorized_client.get(name)
                self.assertEqual(len(response.context['page_obj']), 10)
                page = response.context['page_obj']
                for index in range(10):
                    post_contains_func(self, page, index)

                """А здесь тестируем вторую страницу."""
                response = self.authorized_client.get((name) + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)
                page = response.context['page_obj']
                for index in range(3):
                    post_contains_func(self, page, index)


class OnePostTest(BaseTest):
    """Дополнительная проверка. При создании поста и указания у него
    группы, пост доступен на страницах index, group_list и profile.
    Пост не доступен на странице не своей группы.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_2 = Group.objects.create(
            title='Машины',
            slug='cars',
            description='Тут про машины'
        )

    def test_one_post_with_group_show_on_different_pages(self):
        """Если при создании поста указать группу, то он будет
        доступен на страницах index, group_list и profile."""
        for name in url_names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                self.assertEqual(self.post, response.context['page_obj'][0])

    def test_one_post_with_group_not_show_on_other_group_list_page(self):
        """Пост с указанной группой недоступен на странице другой группы."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'cars'})
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class FollowingTest(BaseTest):
    """Тестируем функции подписки и отписки на авторов."""
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(username='joe')
        self.auth_user_2 = Client()
        self.auth_user_2.force_login(self.other_user)
        self.follow_count = Follow.objects.count()

    def test_auth_user_following(self):
        """Авторизованный юзер может подписаться на автора."""
        self.auth_user_2.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'author'})
        )
        subscription = Follow.objects.filter(
            author=self.user,
            user=self.other_user
        )
        self.assertEqual(Follow.objects.count(), self.follow_count + 1)
        self.assertTrue(subscription.exists())

    def test_follower_can_unsubscribe(self):
        """Подписчик может отписаться от автора."""
        Follow.objects.create(
            author=self.user,
            user=self.other_user
        )
        self.auth_user_2.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': 'author'})
        )
        self.assertEqual(Follow.objects.count(), self.follow_count)
        self.assertFalse(Follow.objects.filter(
            author=self.user,
            user=self.other_user).exists()
        )

    def test_new_post_available_to_subscribers(self):
        """Новый пост появляется в ленте подписчиков."""
        Follow.objects.create(
            author=self.user,
            user=self.other_user
        )
        new_post = Post.objects.create(
            text='Любимый пост подписчиков',
            author=self.user
        )
        response = self.auth_user_2.get(reverse('posts:follow_index'))
        self.assertEqual(new_post, response.context['page_obj'][0])

    def test_non_subscribers_not_see_new_post(self):
        """Неподписанные на автора юзеры не видят новый пост в ленте."""
        Post.objects.create(
            text='Невидимый пост',
            author=self.user
        )
        response = self.auth_user_2.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_prevent_self_followng(self):
        """Автор не может подписаться сам на себя."""
        # Пробуем создать подписку на самого себя. 
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'author'})
        )
        # Проверяем, что подписка не создалась.
        self.assertEqual(Follow.objects.count(), self.follow_count)

    def test_attempt_to_resubscribe(self):
        """Повторно подписаться на автора нельзя."""
        # Создаем подписку вручную.
        Follow.objects.create(
            author=self.user,
            user=self.other_user
        )
        # Пробуем тем же юзером повторно подписаться на автора.
        self.auth_user_2.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'author'})
        )
        # В проверке учитываем, что подписка должна быть лишь одна.
        self.assertEqual(Follow.objects.count(), self.follow_count + 1)
