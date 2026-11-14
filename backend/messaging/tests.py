import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth.models import User
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase

from .models import Conversation, Message


class ConversationApiTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="password")
        self.bob = User.objects.create_user("bob", password="password")
        self.carol = User.objects.create_user("carol", password="password")
        self.client.force_login(self.alice)

    def post_json(self, url, body, client=None):
        return (client or self.client).post(
            url,
            data=json.dumps(body),
            content_type="application/json",
        )

    def conversation(self, first=None, second=None):
        member_one, member_two = sorted(
            (first or self.alice, second or self.bob),
            key=lambda user: user.pk,
        )
        return Conversation.objects.create(
            member_one=member_one,
            member_two=member_two,
        )

    def test_conversation_creation_is_private_and_idempotent_for_user_pair(self):
        first = self.post_json(
            "/api/conversations/",
            {"other_user_id": self.bob.pk},
        )
        second_client = Client()
        second_client.force_login(self.bob)
        second = self.post_json(
            "/api/conversations/",
            {"other_user_id": self.alice.pk},
            client=second_client,
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            first.json()["conversation"]["id"],
            second.json()["conversation"]["id"],
        )
        self.assertEqual(Conversation.objects.count(), 1)

        self_conversation = self.post_json(
            "/api/conversations/",
            {"other_user_id": self.alice.pk},
        )
        self.assertEqual(self_conversation.status_code, 400)

    def test_conversation_list_only_contains_memberships(self):
        shared = self.conversation()
        self.conversation(self.bob, self.carol)

        response = self.client.get("/api/conversations/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.json()["conversations"]],
            [shared.pk],
        )

    def test_anonymous_requests_are_rejected(self):
        anonymous = Client()
        conversation = self.conversation()
        self.assertEqual(anonymous.get("/api/conversations/").status_code, 401)
        self.assertEqual(
            anonymous.get(f"/api/conversations/{conversation.pk}/messages/").status_code,
            401,
        )
        self.assertEqual(
            self.post_json("/api/conversations/", {"other_user_id": self.bob.pk}, anonymous).status_code,
            401,
        )

    def test_messages_are_persisted_ordered_and_trimmed(self):
        conversation = self.conversation()
        first = self.post_json(
            f"/api/conversations/{conversation.pk}/messages/",
            {"content": "  First message  "},
        )
        second = self.post_json(
            f"/api/conversations/{conversation.pk}/messages/",
            {"content": "Second message"},
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()["message"]["content"], "First message")
        self.assertEqual(second.status_code, 201)
        history = self.client.get(
            f"/api/conversations/{conversation.pk}/messages/"
        ).json()["messages"]
        self.assertEqual([message["content"] for message in history], ["First message", "Second message"])
        self.assertEqual(Message.objects.count(), 2)

    def test_blank_and_oversized_messages_are_rejected(self):
        conversation = self.conversation()
        url = f"/api/conversations/{conversation.pk}/messages/"
        blank = self.post_json(url, {"content": "   "})
        too_long = self.post_json(url, {"content": "x" * 4001})
        self.assertEqual(blank.status_code, 400)
        self.assertEqual(too_long.status_code, 400)
        self.assertEqual(Message.objects.count(), 0)

    def test_non_member_cannot_read_or_send_messages_or_read_conversation(self):
        conversation = self.conversation()
        outsider = Client()
        outsider.force_login(self.carol)

        self.assertEqual(
            outsider.get(f"/api/conversations/{conversation.pk}/").status_code,
            404,
        )
        self.assertEqual(
            outsider.get(f"/api/conversations/{conversation.pk}/messages/").status_code,
            404,
        )
        send = self.post_json(
            f"/api/conversations/{conversation.pk}/messages/",
            {"content": "unauthorized"},
            client=outsider,
        )
        self.assertEqual(send.status_code, 404)
        self.assertEqual(Message.objects.count(), 0)

    def test_message_history_cursor_is_validated(self):
        conversation = self.conversation()
        response = self.client.get(
            f"/api/conversations/{conversation.pk}/messages/?before=invalid"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("before", response.json())


class ConcurrentConversationCreationTests(TransactionTestCase):
    reset_sequences = True

    def test_concurrent_requests_create_only_one_conversation(self):
        alice = User.objects.create_user("alice", password="password")
        bob = User.objects.create_user("bob", password="password")
        barrier = Barrier(2)

        def create_conversation(user_id, other_user_id):
            close_old_connections()
            try:
                user = User.objects.get(pk=user_id)
                client = Client()
                client.force_login(user)
                barrier.wait(timeout=10)
                response = client.post(
                    "/api/conversations/",
                    data=json.dumps({"other_user_id": other_user_id}),
                    content_type="application/json",
                )
                return response.status_code, response.json()["conversation"]["id"]
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(
                lambda users: create_conversation(*users),
                ((alice.pk, bob.pk), (bob.pk, alice.pk)),
            ))

        self.assertCountEqual([status for status, _ in results], (200, 201))
        self.assertEqual(results[0][1], results[1][1])
        self.assertEqual(Conversation.objects.count(), 1)
