import shutil
import tempfile

from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, User
from ..settings import POSTS_PER_PAGE

MAIN_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
SLUG = 'test-slug-1'
SLUG2 = 'test-slug-2'
USER = 'logged_user'
POST_ID = 1
GROUP_URL = reverse('posts:group_list', kwargs={'slug': SLUG})
GROUP_URL2 = reverse('posts:group_list', kwargs={'slug': SLUG2})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USER})
POST_CREATE_URL = reverse('posts:post_create')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username=USER)
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug=SLUG,
            description='Тестовое описание 1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 1',
            group=Group.objects.create(
                title='Тестовая группа 2',
                slug=SLUG2,
                description='Тестовое описание 2'),
            image=uploaded
        )
        cls.POST_URL = reverse('posts:post_detail',
                               kwargs={'post_id': cls.post.id})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_pages_show_correct_context(self):
        """Шаблон с постом имеет правильный контекст"""
        urls = [MAIN_URL, GROUP_URL2, PROFILE_URL, self.POST_URL]
        for url in urls:
            with self.subTest(url=url):
                post_context = self.guest_client.get(url).context
                if url != self.POST_URL:
                    self.assertEqual(len(post_context['page_obj']), 1)
                    post = post_context['page_obj'][0]
                else:
                    post = post_context.get('post')
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)
                self.assertEqual(post.comments, self.post.comments)

    def test_author_in_profile_show_correct_context(self):
        """Шаблон с автором имеет правильный контекст"""
        self.assertEqual(self.guest_client.get(PROFILE_URL).
                         context.get('author').username, self.user.username)

    def test_group_in_group_page_show_correct_context(self):
        """Шаблон с группой имеет правильный контекст"""
        group = self.guest_client.get(GROUP_URL).context.get('group')
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description,
                         self.group.description)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.id, self.group.id)

    def test_post_in_right_group(self):
        """Поста нет не в своей группе"""
        self.assertNotIn(self.post, self.authorized_client.get(GROUP_URL).
                         context['page_obj'])

    def test_paginated_navigation_contains_ten_records(self):
        """Постраничная навигация выводит по 10 постов."""
        Post.objects.bulk_create(
            Post(
                author=self.user,
                text=f'Тестовый пост {i}',
                group=self.group,
            )
            for i in range(POSTS_PER_PAGE + 3))
        cases = {
            MAIN_URL: POSTS_PER_PAGE,
            MAIN_URL + '?page=2': 4,
            GROUP_URL: POSTS_PER_PAGE,
            GROUP_URL + '?page=2': 3,
            PROFILE_URL: POSTS_PER_PAGE,
            PROFILE_URL + '?page=2': 4,
        }
        for url, posts_count in cases.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), posts_count
                )
