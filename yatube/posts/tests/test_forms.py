import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

POST_CREATE_URL = reverse('posts:post_create')
SLUG = 'test-slug-1'
SLUG2 = 'test-slug-2'
USER = 'logged_user'
PROFILE_URL = reverse('posts:profile', kwargs={'username': USER})


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER)
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug=SLUG,
            description='Тестовое описание 1',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug=SLUG2,
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 1',
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.id})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.id})
        cls.ADD_COMMENT_URL = reverse('posts:add_comment',
                                      kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts = set(Post.objects.all())
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        posts = set(Post.objects.all()) - posts
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(
            f"{Post._meta.get_field('image').upload_to}{form_data['image']}",
            post.image)
        self.assertEqual(self.user, post.author)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(form_data['text'], post.text)
        self.assertEqual(form_data['group'], post.group.id)
        self.assertEqual(self.user, self.post.author)

    def test_post_create_and_edit_page_correct_context(self):
        """Шаблон post_create и post_edit
        сформированы с правильным контекстом."""
        form_fields = [
            ['text', forms.fields.CharField],
            ['group', forms.fields.ChoiceField]
        ]
        for url in [POST_CREATE_URL, self.POST_EDIT_URL]:
            post_form_context = self.authorized_client.get(
                url).context.get('form')
            for key, type in form_fields:
                with self.subTest(key=key):
                    self.assertIsInstance(
                        post_form_context.fields.get(key), type)

    def test_new_comment_on_post_page(self):
        comments = set(Comment.objects.all())
        form_data = {
            'text': 'Текст комментария 1',
            'post': self.post.id
        }
        response = self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        comments = set(Comment.objects.all()) - comments
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertEqual(len(comments), 1)
        comment = comments.pop()
        self.assertIn(comment, self.authorized_client.get(
            self.POST_DETAIL_URL).context.get('comments'))
