import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse

from ..models import Post, Group, User, Follow
from ..settings import POSTS_PER_PAGE

SLUG = 'test-slug-1'
SLUG2 = 'test-slug-2'
USER = 'logged_user'
FOLLOWER = 'follower'
NONFOLLOWER = 'nonfollower'
POST_ID = 1

GROUP_URL = reverse('posts:group_list', args=[SLUG])
GROUP_URL2 = reverse('posts:group_list', args=[SLUG2])
PROFILE_URL = reverse('posts:profile', args=[USER])
POST_CREATE_URL = reverse('posts:post_create')
FOLLOW_URL = reverse('posts:follow_index')
MAIN_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
POST_URL = reverse('posts:post_detail', args=[POST_ID])
POST_EDIT_URL = reverse('posts:post_edit', args=[POST_ID])
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USER])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USER])

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username=USER)
        cls.follower = User.objects.create_user(username=FOLLOWER)
        cls.nonfollower = User.objects.create_user(username=NONFOLLOWER)
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug=SLUG,
            description='Тестовое описание 1',)
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug=SLUG2,
            description='Тестовое описание 2',)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 1',
            group=cls.group2,
            image=cls.uploaded
        )
        cls.follow = Follow.objects.create(author=cls.user, user=cls.follower)
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower)
        cls.nonfollower_client = Client()
        cls.nonfollower_client.force_login(cls.nonfollower)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_pages_show_correct_context(self):
        """Шаблон с постом имеет правильный контекст"""
        urls = [MAIN_URL, GROUP_URL2, PROFILE_URL, POST_URL, FOLLOW_URL]
        for url in urls:
            with self.subTest(url=url):
                post_context = self.follower_client.get(url).context
                if url != POST_URL:
                    self.assertEqual(len(post_context['page_obj']), 1)
                    post = post_context['page_obj'][0]
                else:
                    post = post_context.get('post')
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_author_in_profile_show_correct_context(self):
        """Шаблон с автором имеет правильный контекст"""
        self.assertEqual(self.guest_client.get(PROFILE_URL).
                         context.get('author'), self.user)

    def test_group_in_group_page_show_correct_context(self):
        """Шаблон с группой имеет правильный контекст"""
        group = self.guest_client.get(GROUP_URL).context.get('group')
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.id, self.group.id)

    def test_post_in_right_group_and_follow(self):
        """Поста нет не в своей группе и подписке"""
        urls = [GROUP_URL, FOLLOW_URL]
        for url in urls:
            self.assertNotIn(self.post, self.authorized_client.get(url).
                             context['page_obj'])

    def test_paginated_navigation_contains_ten_records(self):
        """Постраничная навигация выводит по 10 постов."""
        Post.objects.bulk_create(
            Post(
                author=self.user,
                text=f'Тестовый пост {i}',
                group=self.group2,
            )
            for i in range(POSTS_PER_PAGE + 1))
        urls = [MAIN_URL, GROUP_URL2, PROFILE_URL, FOLLOW_URL]
        for url in urls:
            with self.subTest(url=url):
                response = self.follower_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), POSTS_PER_PAGE
                )
                response2 = self.follower_client.get(url + '?page=2')
                self.assertEqual(len(response2.context['page_obj']), 2)

    def test_cache_index_page(self):
        """Кэширование главной страницы работает"""
        cache1 = self.authorized_client.get(MAIN_URL)
        self.assertEqual(len(cache1.context['page_obj']), 1)
        first_post = cache1.context['page_obj'][0]
        first_post.text = 'Текст изменился'
        first_post.save()
        cache2 = self.authorized_client.get(MAIN_URL)
        self.assertEqual(cache1.content, cache2.content)
        cache.clear()
        cache3 = self.authorized_client.get(MAIN_URL)
        self.assertNotEqual(cache1.content, cache3.content)

    def test_user_can_follow_author(self):
        """Авторизованный пользователь может подписываться
        на авторов"""
        follow_count = Follow.objects.count()
        self.nonfollower_client.post(PROFILE_FOLLOW_URL)
        follow = Follow.objects.filter(user=self.nonfollower, author=self.user)
        self.assertTrue(follow.exists())
        self.assertEqual(len(follow), 1)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(follow.author_id, self.user.id)
        self.assertEqual(follow.user_id, self.nonfollower.id)

    def test_user_can_follow_author(self):
        """Авторизованный пользователь может удалять авторов из подписок"""
        follow_count = Follow.objects.count()
        self.follower_client.post(PROFILE_UNFOLLOW_URL)
        self.assertEqual(Follow.objects.count(), follow_count - 1)
