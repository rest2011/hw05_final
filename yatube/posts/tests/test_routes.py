from django.test import TestCase
from django.urls import reverse

from ..urls import app_name

SLUG = 'test-slug-1'
USER = 'logged_user'
POST_ID = 1

ROUTES_URLS = [
    ['index', [], '/'],
    ['group_list', [SLUG], f'/group/{SLUG}/'],
    ['profile', [USER], f'/profile/{USER}/'],
    ['post_detail', [POST_ID], f'/posts/{POST_ID}/'],
    ['post_edit', [POST_ID], f'/posts/{POST_ID}/edit/'],
    ['post_create', [], '/create/'],
    ['follow_index', [], '/follow/'],
    ['add_comment', [POST_ID], f'/posts/{POST_ID}/comment/'],
    ['profile_follow', [USER], f'/profile/{USER}/follow/'],
    ['profile_unfollow', [USER], f'/profile/{USER}/unfollow/']
]


class RoutesTests(TestCase):
    def test_calc_urls_uses_correct_urls(self):
        """Рассчитанные URL соответствуют рельным URL."""
        for route, args, url in ROUTES_URLS:
            with self.subTest(route=route):
                self.assertEqual(reverse(
                    f'{app_name}:{route}', args=args), url)
