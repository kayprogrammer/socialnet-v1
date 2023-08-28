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
        auth_token = TestUtil.auth_token(verified_user)
        self.bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}

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

    def test_create_post(self):
        post_dict = {"text": "My new Post"}
        response = self.client.post(self.posts_url, data=post_dict, **self.bearer)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Post created",
                "data": {
                    "author": mock.ANY,
                    "text": post_dict["text"],
                    "slug": mock.ANY,
                    "created_at": mock.ANY,
                    "updated_at": mock.ANY,
                    "file_upload_data": None,
                },
            },
        )
