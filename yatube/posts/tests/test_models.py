from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тестируем модели приложения Post."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Группа для теста',
            slug='test_slug',
            description='Описание для теста',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста для теста',
        )

    def test_models_post_str_method(self):
        """Проверяем, что у класса Post корректно работает метод __str__."""
        expected_object_name = self.post.text[:15]
        self.assertEqual(expected_object_name, str(self.post))

    def test_models_group_str_method(self):
        """Проверяем, что у класса Group корректно работает метод __str__."""
        expected_object_name = self.group.title
        self.assertEqual(expected_object_name, str(self.group))

    def test_verbose_name(self):
        """Проверям, что verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа'
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """Проверяем, что help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Укажите группу'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value
                )
