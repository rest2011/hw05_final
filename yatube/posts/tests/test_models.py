from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field_strs = {
            str(self.post): self.post.text[:15],
            str(self.group): self.group.title,
        }
        for field, expected_value in field_strs.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field, expected_value)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            Post._meta.get_field('text').verbose_name: 'Текст поста',
            Post._meta.get_field('author').verbose_name: 'Автор',
            Post._meta.get_field('group').verbose_name: 'Группа',
            Group._meta.get_field('title').verbose_name: 'Название',
            Group._meta.get_field('description').verbose_name: 'Описание',
            Group._meta.get_field('slug').verbose_name: 'Идентификатор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    value, expected)

    def test_help_text(self):
        """help_name в полях совпадает с ожидаемым."""
        field_help_text = {
            Post._meta.get_field('text').help_text: 'Текст нового поста',
            Post._meta.get_field('author').help_text: 'Имя автора',
            Post._meta.get_field('group').help_text:
                'Группа, к которой будет относиться пост',
            Group._meta.get_field('title').help_text: 'Название группы',
            Group._meta.get_field('description').help_text: 'Текст описания',
            Group._meta.get_field('slug').help_text: 'Название идентификатора',
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    value, expected)
