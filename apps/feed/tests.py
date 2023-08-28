from rest_framework.test import APITestCase
from unittest import mock
from apps.feed.models import Post
from apps.common.utils import TestUtil


class TestFeed(APITestCase):
    posts_url = "/api/v1/feed/posts/"
    maxDiff = None

    def setUp(self):
        verified_user = TestUtil.verified_user()
        post = Post.objects.create(
            author=verified_user, text="This is a nice new platform"
        )
        self.post = post

    def test_retrieve_posts(self):
        post = self.post
        response = self.client.get(self.posts_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Posts fetched",
                "data": [
                    {
                        "author": mock.ANY,
                        "text": post.text,
                        "slug": f"{post.author.first_name}-{post.author.last_name}-{post.id}".lower(),
                        "reactions_count": 0,
                        "image": None,
                        "created_at": mock.ANY,
                        "updated_at": mock.ANY,
                    }
                ],
            },
        )
