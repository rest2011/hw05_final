from django.test import TestCase

from ..models import Group, Post, User, Comment, Follow, SUBSCRIPTION

USER = 'logged_user'
AUTHOR = 'author'


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER)
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый пост',
            author=cls.author
        )
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        field_strs = {
            str(self.post): self.post.text[:15],
            str(self.group): self.group.title,
            str(self.comment): self.comment.text[:15],
            str(self.follow): SUBSCRIPTION.format(
                user=self.user.username, author=self.author.username),
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
            Post._meta.get_field('image').verbose_name: 'Картинка',
            Group._meta.get_field('title').verbose_name: 'Название',
            Group._meta.get_field('description').verbose_name: 'Описание',
            Group._meta.get_field('slug').verbose_name: 'Идентификатор',
            Comment._meta.get_field('post').verbose_name: 'Пост',
            Comment._meta.get_field('author').verbose_name: 'Автор',
            Comment._meta.get_field('text').verbose_name: 'Текст комментария',
            Follow._meta.get_field('author').verbose_name: 'Автор',
            Follow._meta.get_field('user').verbose_name: 'Подписчик',
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
            Post._meta.get_field('image').help_text:
                'Поле для загрузки картинки',
            Group._meta.get_field('title').help_text: 'Название группы',
            Group._meta.get_field('description').help_text: 'Текст описания',
            Group._meta.get_field('slug').help_text: 'Название идентификатора',
            Comment._meta.get_field('post').help_text: 'Пост для комментария',
            Comment._meta.get_field('author').help_text: 'Имя автора',
            Comment._meta.get_field('text').help_text:
                'Текст нового комментария',
            Follow._meta.get_field('author').help_text: 'Имя автора',
            Follow._meta.get_field('user').help_text: 'Имя подписчика',
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    value, expected)
