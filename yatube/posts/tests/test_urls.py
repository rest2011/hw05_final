from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User

MAIN_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
SLUG = 'test-slug-1'
AUTHOR = 'author'
USER = 'user'
GROUP_URL = reverse('posts:group_list', kwargs={'slug': SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USER})
LOGIN_URL = reverse('users:login')
UNEXISTING_URL = '/unexisting_page/'


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
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.id})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.id})
        cls.POST_EDIT_TO_LOGIN_REDIRECT = (
            f'{LOGIN_URL}?next={cls.POST_EDIT_URL}'
        )
        cls.POST_CREATE_TO_LOGIN_REDIRECT = (
            f'{LOGIN_URL}?next={POST_CREATE_URL}'
        )
        cls.ADD_COMMENT_URL = reverse('posts:add_comment',
                                      kwargs={'post_id': cls.post.id})
        cls.ADD_COMMENT_TO_LOGIN_REDIRECT = (
            f'{LOGIN_URL}?next={cls.ADD_COMMENT_URL}'
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_pages_status(self):
        """Страницы возвращают правильный статус"""
        pages_status = [
            [MAIN_URL, self.guest_client, 200],
            [GROUP_URL, self.guest_client, 200],
            [PROFILE_URL, self.guest_client, 200],
            [POST_CREATE_URL, self.user_client, 200],
            [UNEXISTING_URL, self.guest_client, 404],
            [self.POST_DETAIL_URL, self.guest_client, 200],
            [self.POST_EDIT_URL, self.guest_client, 302],
            [POST_CREATE_URL, self.guest_client, 302],
            [self.POST_EDIT_URL, self.user_client, 302],
            [self.ADD_COMMENT_URL, self.guest_client, 302],
            [self.ADD_COMMENT_URL, self.user_client, 302]
        ]
        for url, client, status_code in pages_status:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code,
                                 status_code)

    def test_redirects(self):
        """Редиректы работают правильно"""
        redirects = [
            [self.POST_EDIT_URL, self.guest_client,
             self.POST_EDIT_TO_LOGIN_REDIRECT],
            [POST_CREATE_URL, self.guest_client,
             self.POST_CREATE_TO_LOGIN_REDIRECT],
            [self.POST_EDIT_URL, self.user_client,
             self.POST_DETAIL_URL],
            [self.ADD_COMMENT_URL, self.guest_client,
             self.ADD_COMMENT_TO_LOGIN_REDIRECT],
            [self.ADD_COMMENT_URL, self.user_client,
             self.POST_DETAIL_URL]
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
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            POST_CREATE_URL: 'posts/create_post.html',
            UNEXISTING_URL: 'core/404.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    self.author_client.get(url), template
                )
