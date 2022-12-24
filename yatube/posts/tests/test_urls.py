from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User


SLUG = 'test-slug-1'
AUTHOR = 'author'
USER = 'user'
POST_ID = 1

MAIN_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_URL = reverse('posts:group_list', args=[SLUG])
PROFILE_URL = reverse('posts:profile', args=[USER])
LOGIN_URL = reverse('users:login')
UNEXISTING_URL = '/unexisting_page/'
POST_DETAIL_URL = reverse('posts:post_detail', args=[POST_ID])
POST_EDIT_URL = reverse('posts:post_edit', args=[POST_ID])
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow', args=[USER])
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow', args=[USER])
POST_EDIT_TO_LOGIN_REDIRECT = (f'{LOGIN_URL}?next={POST_EDIT_URL}')
POST_CREATE_TO_LOGIN_REDIRECT = (f'{LOGIN_URL}?next={POST_CREATE_URL}')
FOLLOW_TO_LOGIN_REDIRECT = (f'{LOGIN_URL}?next={FOLLOW_URL}')
PROFILE_FOLLOW_TO_LOGIN_REDIRECT = (f'{LOGIN_URL}?next={PROFILE_FOLLOW_URL}')
PROFILE_UNFOLLOW_TO_LOGIN_REDIRECT = (
    f'{LOGIN_URL}?next={PROFILE_UNFOLLOW_URL}'
)


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR)
        cls.user = User.objects.create_user(username=USER)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.guest_client = Client()
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)

    def test_pages_status(self):
        """Страницы возвращают правильный статус"""
        pages_status = [
            [MAIN_URL, self.guest_client, 200],
            [GROUP_URL, self.guest_client, 200],
            [PROFILE_URL, self.guest_client, 200],
            [POST_CREATE_URL, self.user_client, 200],
            [UNEXISTING_URL, self.guest_client, 404],
            [POST_DETAIL_URL, self.guest_client, 200],
            [POST_EDIT_URL, self.guest_client, 302],
            [POST_CREATE_URL, self.guest_client, 302],
            [POST_EDIT_URL, self.user_client, 302],
            [FOLLOW_URL, self.guest_client, 302],
            [FOLLOW_URL, self.user_client, 200],
            [PROFILE_FOLLOW_URL, self.author_client, 302],
            [PROFILE_UNFOLLOW_URL, self.author_client, 302],
            [PROFILE_FOLLOW_URL, self.user_client, 302],
            [PROFILE_UNFOLLOW_URL, self.user_client, 404],
            [PROFILE_FOLLOW_URL, self.guest_client, 302],
            [PROFILE_UNFOLLOW_URL, self.guest_client, 302]
        ]
        for url, client, status_code in pages_status:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code,
                                 status_code)

    def test_redirects(self):
        """Редиректы работают правильно"""
        redirects = [
            [POST_EDIT_URL, self.guest_client, POST_EDIT_TO_LOGIN_REDIRECT],
            [POST_CREATE_URL, self.guest_client,
             POST_CREATE_TO_LOGIN_REDIRECT],
            [POST_EDIT_URL, self.user_client, POST_DETAIL_URL],
            [FOLLOW_URL, self.guest_client, FOLLOW_TO_LOGIN_REDIRECT],
            [PROFILE_FOLLOW_URL, self.guest_client,
             PROFILE_FOLLOW_TO_LOGIN_REDIRECT],
            [PROFILE_UNFOLLOW_URL, self.guest_client,
             PROFILE_UNFOLLOW_TO_LOGIN_REDIRECT],
            [PROFILE_FOLLOW_URL, self.user_client, PROFILE_URL],
            [PROFILE_FOLLOW_URL, self.author_client, PROFILE_URL],
            [PROFILE_UNFOLLOW_URL, self.author_client, PROFILE_URL]
        ]
        for url, client, redirect in redirects:
            with self.subTest(url=url, client=client):
                self.assertRedirects(client.get(url), redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            MAIN_URL: 'posts/index.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            POST_DETAIL_URL: 'posts/post_detail.html',
            POST_EDIT_URL: 'posts/create_post.html',
            POST_CREATE_URL: 'posts/create_post.html',
            UNEXISTING_URL: 'core/404.html',
            FOLLOW_URL: 'posts/follow.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author_client.get(url), template
                )
