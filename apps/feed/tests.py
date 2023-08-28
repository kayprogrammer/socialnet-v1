from rest_framework.test import APITestCase
from unittest import mock
from apps.feed.models import Post
from apps.common.utils import TestUtil
from apps.common.error import ErrorCode


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
        another_verified_user = TestUtil.another_verified_user()
        auth_token = TestUtil.auth_token(another_verified_user)
        self.other_user_bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}

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
                        "slug": post.slug,
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

    def test_retrieve_post(self):
        post = self.post

        # Test for post with invalid slug
        response = self.client.get(f"{self.posts_url}invalid-slug/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.NON_EXISTENT,
                "message": "No post with that slug",
            },
        )

        # Test for post with valid slug
        response = self.client.get(f"{self.posts_url}{post.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Post Detail fetched",
                "data": {
                    "author": mock.ANY,
                    "text": post.text,
                    "slug": post.slug,
                    "reactions_count": 0,
                    "image": None,
                    "created_at": mock.ANY,
                    "updated_at": mock.ANY,
                },
            },
        )

    def test_update_post(self):
        post_dict = {"text": "Post Text Updated"}
        post = self.post
        # Check if endpoint fails for invalid post
        response = self.client.put(
            f"{self.posts_url}invalid-slug/", data=post_dict, **self.bearer
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.NON_EXISTENT,
                "message": "No post with that slug",
            },
        )

        # Check if endpoint fails for invalid owner
        response = self.client.put(
            f"{self.posts_url}{post.slug}/", data=post_dict, **self.other_user_bearer
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "code": ErrorCode.INVALID_OWNER,
                "message": "This Post isn't yours",
            },
        )

        # Check if endpoint succeeds if all requirements are met
        response = self.client.put(
            f"{self.posts_url}{post.slug}/", data=post_dict, **self.bearer
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Post updated",
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
