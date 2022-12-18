from django.test import TestCase
from django.urls import reverse

SLUG = 'test-slug-1'
USER = 'logged_user'
POST_ID = 1

ROUTES_URLS = [
    ['index', {}, '/'],
    ['group_list', {'slug': SLUG}, f'/group/{SLUG}/'],
    ['profile', {'username': USER}, f'/profile/{USER}/'],
    ['post_detail', {'post_id': POST_ID}, f'/posts/{POST_ID}/'],
    ['post_edit', {'post_id': POST_ID}, f'/posts/{POST_ID}/edit/'],
    ['post_create', {}, '/create/']
]


class RoutesTests(TestCase):
    def test_calc_urls_uses_correct_urls(self):
        """Рассчитанные URL соответствуют рельным URL."""
        for route, kwargs, url in ROUTES_URLS:
            with self.subTest(route=route):
                self.assertEqual(reverse(f'posts:{route}', kwargs=kwargs), url)
