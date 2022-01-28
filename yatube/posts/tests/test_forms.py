import shutil
import tempfile

from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

User = get_user_model()

OK = HTTPStatus.OK

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class BaseClassFormTest(TestCase):
    """Базовый класс для тестов форм."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def setUp(self):
        test_image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.image = SimpleUploadedFile(
            name='test.gif',
            content=test_image,
            content_type='image/gif'
        )

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


class PostFormTest(BaseClassFormTest):
    """Тестируем форму создания и редактирования поста."""
    def test_create_new_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст второго поста',
            'group': self.group.id,
            'image': self.image
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group,
                author=self.user,
                image='posts/test.gif'
            ).exists()
        )

    def test_create_new_post_without_text(self):
        """При пустом поле text поста форма выдает ошибку."""
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(response.status_code, OK)

    def test_post_edit(self):
        """Валидная форма редактирует существующий пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст поста',
            'group': self.group.id,
            'post_id': self.post.id,
            'image': self.image
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group,
                author=self.user,
                image='posts/test.gif'
            ).exists()
        )

    def test_post_edit_without_text(self):
        """При редактировании поста с пустым полем
        text получаем ошибку."""
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': self.group.id,
            'post_id': self.post.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            'Обязательное поле.'
        )
        self.assertEqual(response.status_code, OK)


class CommentFormTest(BaseClassFormTest):
    """Тестируем форму для создания комментариев."""
    def setUp(self):
        self.form_data = {
            'post': self.post,
            'author': self.user,
            'text': 'Первый коммент'
        }
        self.comments_count = Comment.objects.count()

    def test_comments_only_for_authorized_users(self):
        """Комментировать могут только авторизованные пользователи."""
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), self.comments_count)

    def test_create_new_comment(self):
        """После отправки коммент появляется на странице поста."""
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), self.comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=self.form_data['text'],
                post=self.post,
                author=self.user
            ).exists()
        )
