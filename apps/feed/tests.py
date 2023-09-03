from rest_framework.test import APITestCase
from unittest import mock
from apps.feed.models import Post, Reaction, Comment, Reply
from apps.common.utils import TestUtil
from apps.common.error import ErrorCode
import uuid


class TestFeed(APITestCase):
    posts_url = "/api/v1/feed/posts/"
    reactions_url = "/api/v1/feed/reactions/"
    comment_url = "/api/v1/feed/comments/"

    maxDiff = None

    def setUp(self):
        # user
        verified_user = TestUtil.verified_user()
        another_verified_user = TestUtil.another_verified_user()
        self.verified_user = verified_user

        # post
        post = Post.objects.create(
            author=verified_user, text="This is a nice new platform"
        )
        self.post = post

        # auth
        auth_token = TestUtil.auth_token(verified_user)
        self.bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}
        auth_token = TestUtil.auth_token(another_verified_user)
        self.other_user_bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}

        # reaction
        self.reaction = Reaction.objects.create(
            user=verified_user, rtype="LIKE", post=post
        )

        # comment
        comment = Comment.objects.create(
            author=verified_user, post=post, text="Just a comment"
        )
        self.comment = comment

        # reply
        self.reply = Reply.objects.create(
            author=verified_user, comment=comment, text="Simple reply"
        )

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
                        "reactions_count": mock.ANY,
                        "comments_count": mock.ANY,
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
                    "reactions_count": mock.ANY,
                    "comments_count": mock.ANY,
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

    def test_delete_post(self):
        post = self.post
        # Check if endpoint fails for invalid post
        response = self.client.delete(f"{self.posts_url}invalid-slug/", **self.bearer)
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
        response = self.client.delete(
            f"{self.posts_url}{post.slug}/", **self.other_user_bearer
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
        response = self.client.delete(f"{self.posts_url}{post.slug}/", **self.bearer)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Post deleted",
            },
        )

    def test_retrieve_reactions(self):
        post = self.post
        user = self.verified_user
        reaction = self.reaction

        # Test for invalid for_value
        response = self.client.get(f"{self.reactions_url}invalid_for/{post.slug}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Invalid 'for' value",
                "code": ErrorCode.INVALID_VALUE,
            },
        )

        # Test for invalid slug
        response = self.client.get(f"{self.reactions_url}POST/invalid_slug/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Post does not exist",
                "code": ErrorCode.NON_EXISTENT,
            },
        )

        # Test for valid values
        response = self.client.get(f"{self.reactions_url}POST/{post.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Reactions fetched",
                "data": [
                    {
                        "id": str(reaction.id),
                        "user": {
                            "name": user.full_name,
                            "slug": user.username,
                            "avatar": user.get_avatar,
                        },
                        "rtype": reaction.rtype,
                    }
                ],
            },
        )

    def test_create_reaction(self):
        post = self.post
        user = self.verified_user

        reaction_data = {"rtype": "LOVE"}

        # Test for invalid for_value
        response = self.client.post(
            f"{self.reactions_url}invalid_for/{post.slug}/",
            data=reaction_data,
            **self.bearer,
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Invalid 'for' value",
                "code": ErrorCode.INVALID_VALUE,
            },
        )

        # Test for invalid slug
        response = self.client.post(
            f"{self.reactions_url}POST/invalid_slug/", data=reaction_data, **self.bearer
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Post does not exist",
                "code": ErrorCode.NON_EXISTENT,
            },
        )

        # Test for valid values
        response = self.client.post(
            f"{self.reactions_url}POST/{post.slug}/", data=reaction_data, **self.bearer
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Reaction created",
                "data": {
                    "id": mock.ANY,
                    "user": {
                        "name": user.full_name,
                        "slug": user.username,
                        "avatar": user.get_avatar,
                    },
                    "rtype": reaction_data["rtype"],
                },
            },
        )

    def test_delete_reaction(self):
        reaction = self.reaction

        # Test for invalid reaction id
        invalid_id = str(uuid.uuid4())
        response = self.client.delete(
            f"{self.reactions_url}{invalid_id}/", **self.bearer
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Reaction does not exist",
                "code": ErrorCode.NON_EXISTENT,
            },
        )

        # Test for invalid owner
        response = self.client.delete(
            f"{self.reactions_url}{reaction.id}/", **self.other_user_bearer
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Not yours to delete",
                "code": ErrorCode.INVALID_OWNER,
            },
        )

        # Test for valid values
        response = self.client.delete(
            f"{self.reactions_url}{reaction.id}/", **self.bearer
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Reaction deleted",
            },
        )

    def test_retrieve_comments(self):
        comment = self.comment
        post = self.post
        user = self.verified_user

        # Test for invalid post slug
        response = self.client.get(f"{self.posts_url}invalid_slug/comments/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Post does not exist",
                "code": ErrorCode.NON_EXISTENT,
            },
        )

        # Test for valid values
        response = self.client.get(f"{self.posts_url}{post.slug}/comments/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Comments Fetched",
                "data": [
                    {
                        "author": {
                            "name": user.full_name,
                            "slug": user.username,
                            "avatar": user.get_avatar,
                        },
                        "slug": comment.slug,
                        "text": comment.text,
                        "replies_count": comment.replies.count(),
                    }
                ],
            },
        )

    def test_create_comment(self):
        post = self.post
        user = self.verified_user

        comment_data = {"text": "My new comment"}

        # Test for invalid slug
        response = self.client.post(
            f"{self.posts_url}invalid_slug/comments/", data=comment_data, **self.bearer
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Post does not exist",
                "code": ErrorCode.NON_EXISTENT,
            },
        )

        # Test for valid values
        response = self.client.post(
            f"{self.posts_url}{post.slug}/comments/", data=comment_data, **self.bearer
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Comment Created",
                "data": {
                    "author": {
                        "name": user.full_name,
                        "slug": user.username,
                        "avatar": user.get_avatar,
                    },
                    "slug": mock.ANY,
                    "text": comment_data["text"],
                    "replies_count": 0,
                },
            },
        )

    def test_retrieve_comment_with_replies(self):
        reply = self.reply
        comment = reply.comment
        user = self.verified_user

        # Test for invalid comment slug
        response = self.client.get(f"{self.comment_url}invalid_slug/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "Comment does not exist",
                "code": ErrorCode.NON_EXISTENT,
            },
        )

        # Test for valid values
        response = self.client.get(f"{self.comment_url}{comment.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Comment and Replies Fetched",
                "data": {
                    "comment": {
                        "author": {
                            "name": user.full_name,
                            "slug": user.username,
                            "avatar": user.get_avatar,
                        },
                        "slug": comment.slug,
                        "text": comment.text,
                        "replies_count": comment.replies.count(),
                    },
                    "replies": [
                        {
                            "author": {
                                "name": user.full_name,
                                "slug": user.username,
                                "avatar": user.get_avatar,
                            },
                            "slug": reply.slug,
                            "text": reply.text,
                        }
                    ],
                },
            },
        )
