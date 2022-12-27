import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SLUG = 'test-slug-1'
SLUG2 = 'test-slug-2'
USER = 'logged_user'
NONAUTHOR = 'nonauthor'
LOGIN_URL = reverse('users:login')
POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=[USER])
POST_CREATE_TO_LOGIN_REDIRECT = f'{LOGIN_URL}?next={POST_CREATE_URL}'

UPLOAD_TO = Post._meta.get_field('image').upload_to

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.user = User.objects.create_user(username=USER)
        cls.nonauthor = User.objects.create_user(username=NONAUTHOR)
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
            group=cls.group,
            image=SimpleUploadedFile(
                name='small.gif',
                content=SMALL_GIF,
                content_type='image/gif'
            ),
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      args=[cls.post.id])
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    args=[cls.post.id])
        cls.ADD_COMMENT_URL = reverse('posts:add_comment',
                                      args=[cls.post.id])
        cls.ADD_COMMENT_TO_LOGIN_REDIRECT = (
            f'{LOGIN_URL}?next={cls.ADD_COMMENT_URL}'
        )
        cls.POST_EDIT_TO_LOGIN_REDIRECT = (
            f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.nonauthor_client = Client()
        cls.nonauthor_client.force_login(cls.nonauthor)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts = set(Post.objects.all())
        uploaded2 = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': uploaded2,
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
        self.assertEqual(f"{UPLOAD_TO}{form_data['image']}", post.image)
        self.assertEqual(self.user, post.author)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        uploaded3 = SimpleUploadedFile(
            name='small3.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.group2.id,
            'image': uploaded3,
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
        self.assertEqual(f"{UPLOAD_TO}{form_data['image']}", post.image)
        self.assertEqual(self.user, self.post.author)

    def test_post_create_and_edit_page_correct_context(self):
        """Шаблон post_create и post_edit
        сформированы с правильным контекстом."""
        form_fields = [
            ['text', forms.fields.CharField],
            ['group', forms.fields.ChoiceField],
            ['image', forms.fields.ImageField]
        ]
        for url in [POST_CREATE_URL, self.POST_EDIT_URL]:
            post_form_context = self.authorized_client.get(
                url).context.get('form')
            for key, type in form_fields:
                with self.subTest(key=key):
                    self.assertIsInstance(
                        post_form_context.fields.get(key), type)

    def test_new_comment_on_post_page(self):
        """Опубликованный комментарий появляется на странице поста"""
        comments = set(Comment.objects.all())
        form_data = {
            'text': 'Текст комментария 1'
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
        self.assertEqual(form_data['text'], comment.text)
        self.assertEqual(self.post, comment.post)
        self.assertEqual(self.user, comment.author)

    def test_guest_cant_create_comment_or_post(self):
        """Гость не может создать комментарий или пост"""
        form_data_comment = {
            'text': 'Текст комментария 1'
        }
        uploaded2 = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data_post = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': uploaded2,
        }
        urls = [
            [POST_CREATE_URL, Post,
             POST_CREATE_TO_LOGIN_REDIRECT, form_data_post],
            [self.ADD_COMMENT_URL, Comment,
             self.ADD_COMMENT_TO_LOGIN_REDIRECT, form_data_comment]
        ]
        for url, class_, redirect, form_data in urls:
            with self.subTest(url=url):
                objects_before_posting = set(class_.objects.all())
                response = self.guest_client.post(url, data=form_data,
                                                  follow=True)
                self.assertRedirects(response, redirect)
                self.assertEqual(set(class_.objects.all()),
                                 objects_before_posting)

    def test_guest_or_nonauthor_cant_update_post(self):
        """Гость или неавтор не могут редактировать пост"""
        uploaded3 = SimpleUploadedFile(
            name='small3.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.group2.id,
            'image': uploaded3,
        }
        clients = [
            [self.guest_client, self.POST_EDIT_TO_LOGIN_REDIRECT],
            [self.nonauthor_client, self.POST_DETAIL_URL]
        ]
        for client, redirect in clients:
            with self.subTest(client=client):
                response = client.post(
                    self.POST_EDIT_URL, data=form_data, follow=True)
                post = Post.objects.get(id=self.post.id)
                self.assertRedirects(response, redirect)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.image, self.post.image)
