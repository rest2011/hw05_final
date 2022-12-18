from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User, Follow

SLUG = 'test-slug-1'
FOLLOWER = 'follower'
NONFOLLOWER = 'nonfollower'
AUTHOR = 'author'
FOLLOW_URL = reverse('posts:follow_index')


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.follower = User.objects.create_user(username=FOLLOWER)
        cls.nonfollower = User.objects.create_user(username=NONFOLLOWER)
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug=SLUG,
            description='Тестовое описание 1',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост 1',
            group=cls.group
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.nonfollower_client = Client()
        self.nonfollower_client.force_login(self.nonfollower)

    def test_user_can_follow_unfollow_author(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок"""
        follow = Follow.objects.create(author=self.author, user=self.follower)
        follow = Follow.objects.filter(author=self.author, user=self.follower)
        self.assertTrue(follow.exists())
        follow.delete()
        self.assertFalse(follow.exists())

    def test_author_post_in_follower_page(self):
        """Новая запись пользователя появляется
        в ленте тех, кто на него подписан"""
        Follow.objects.create(author=self.author, user=self.follower)
        post = self.follower_client.get(FOLLOW_URL).context['page_obj'][0]
        self.assertEqual(post.id, self.post.id)

    def test_author_post_not_in_unfollower_page(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто на него не подписан"""
        follow = Follow.objects.filter(author=self.author,
                                       user=self.nonfollower)
        self.assertFalse(follow.exists())
        posts = self.nonfollower_client.get(FOLLOW_URL).context['page_obj']
        self.assertNotIn(self.post, posts)
