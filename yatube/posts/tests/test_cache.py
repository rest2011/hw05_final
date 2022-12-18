from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User

MAIN_URL = reverse('posts:index')
SLUG = 'test-slug-1'
USER = 'logged_user'


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USER)
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug=SLUG,
            description='Тестовое описание 1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост 1',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()

    def test_cache_index_page(self):
        """Кэширование главной страницы работает"""
        response = self.guest_client.get(MAIN_URL)
        cache = response.content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(MAIN_URL)
        cache2 = response2.content
        self.assertEqual(cache, cache2)
