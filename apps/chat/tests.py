from rest_framework.test import APITestCase
from unittest import mock
from apps.chat.models import Chat, Message
from apps.common.utils import TestUtil
from apps.common.error import ErrorCode
import uuid


class TestFeed(APITestCase):
    chats_url = "/api/v1/chats/"
    messages_url = "/api/v1/chats/messages/"
    groups_url = "/api/v1/chats/groups/group/"

    maxDiff = None

    def setUp(self):
        # user
        verified_user = TestUtil.verified_user()
        another_verified_user = TestUtil.another_verified_user()
        self.verified_user = verified_user

        # chat & message
        chat = Chat.objects.create(owner=verified_user)
        chat.users.add(another_verified_user)
        message = Message.objects.create(
            chat=chat, sender=verified_user, text="Hello Boss"
        )
        self.chat = chat
        self.message = message

        # auth
        auth_token = TestUtil.auth_token(verified_user)
        self.bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}
        auth_token = TestUtil.auth_token(another_verified_user)
        self.other_user_bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}

    def test_retrieve_chats(self):
        chat = self.chat
        message = self.message
        response = self.client.get(self.chats_url, **self.bearer)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Chats fetched",
                "data": [
                    {
                        "id": str(chat.id),
                        "name": chat.name,
                        "owner": mock.ANY,
                        "ctype": chat.ctype,
                        "description": chat.description,
                        "image": chat.get_image,
                        "latest_message": {
                            "sender": mock.ANY,
                            "text": message.text,
                            "file": message.get_file,
                        },
                        "created_at": mock.ANY,
                        "updated_at": mock.ANY,
                    }
                ],
            },
        )
