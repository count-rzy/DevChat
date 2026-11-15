import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch

from asgiref.sync import async_to_sync, sync_to_async
from django.contrib.auth.models import User
from django.conf import settings
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone
from channels.testing import WebsocketCommunicator

from config.asgi import application

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


class MessageOperationsApiTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="password")
        self.bob = User.objects.create_user("bob", password="password")
        self.carol = User.objects.create_user("carol", password="password")
        self.conversation = self.create_conversation(self.alice, self.bob)
        self.other_conversation = self.create_conversation(self.alice, self.carol)
        self.client.force_login(self.alice)

    @staticmethod
    def create_conversation(first, second):
        first, second = sorted((first, second), key=lambda user: user.pk)
        return Conversation.objects.create(member_one=first, member_two=second)

    @staticmethod
    def post_json(client, url, payload):
        return client.post(url, data=json.dumps(payload), content_type="application/json")

    @staticmethod
    def patch_json(client, url, payload):
        return client.patch(url, data=json.dumps(payload), content_type="application/json")

    def message_url(self, message_id):
        return f"/api/conversations/{self.conversation.pk}/messages/{message_id}/"

    def test_only_author_can_edit_and_deleted_messages_become_tombstones(self):
        created = self.post_json(
            self.client,
            f"/api/conversations/{self.conversation.pk}/messages/",
            {"content": "original"},
        )
        message_id = created.json()["message"]["id"]

        edited = self.patch_json(
            self.client,
            self.message_url(message_id),
            {"content": "  corrected  "},
        )
        self.assertEqual(edited.status_code, 200)
        self.assertEqual(edited.json()["message"]["content"], "corrected")
        self.assertIsNotNone(edited.json()["message"]["edited_at"])

        bob_client = Client()
        bob_client.force_login(self.bob)
        denied_edit = self.patch_json(
            bob_client,
            self.message_url(message_id),
            {"content": "hijacked"},
        )
        self.assertEqual(denied_edit.status_code, 403)

        deleted = self.client.delete(self.message_url(message_id))
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(deleted.json()["message"]["content"], "")
        self.assertIsNotNone(deleted.json()["message"]["deleted_at"])
        self.assertEqual(Message.objects.get(pk=message_id).content, "")
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(
            self.client.get(self.message_url(message_id)).status_code,
            405,
        )
        blocked_edit = self.patch_json(
            self.client,
            self.message_url(message_id),
            {"content": "restore"},
        )
        self.assertEqual(blocked_edit.status_code, 400)

    def test_replies_require_a_message_in_the_same_conversation(self):
        original = Message.objects.create(
            conversation=self.conversation,
            sender=self.bob,
            content="answer this",
        )
        created = self.post_json(
            self.client,
            f"/api/conversations/{self.conversation.pk}/messages/",
            {"content": "my reply", "reply_to_id": original.pk},
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()["message"]["reply_to"]["content"], "answer this")
        self.assertEqual(created.json()["message"]["reply_to"]["sender_name"], "bob")

        inaccessible = Message.objects.create(
            conversation=self.other_conversation,
            sender=self.carol,
            content="not in this chat",
        )
        cross_conversation_reply = self.post_json(
            self.client,
            f"/api/conversations/{self.conversation.pk}/messages/",
            {"content": "bad reference", "reply_to_id": inaccessible.pk},
        )
        self.assertEqual(cross_conversation_reply.status_code, 404)

        original.deleted_at = timezone.now()
        original.content = ""
        original.save(update_fields=["content", "deleted_at"])
        history = self.client.get(
            f"/api/conversations/{self.conversation.pk}/messages/"
        ).json()["messages"]
        reply = next(item for item in history if item["id"] == created.json()["message"]["id"])
        self.assertTrue(reply["reply_to"]["deleted"])
        self.assertIsNone(reply["reply_to"]["content"])

    def test_reactions_toggle_and_are_private_to_conversation_members(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.bob,
            content="react to this",
        )
        url = f"{self.message_url(message.pk)}reactions/"
        first = self.post_json(self.client, url, {"emoji": "👍"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(
            first.json()["message"]["reactions"],
            [{"emoji": "👍", "count": 1, "reacted": True}],
        )
        second = self.post_json(self.client, url, {"emoji": "👍"})
        self.assertEqual(second.json()["message"]["reactions"], [])
        invalid = self.post_json(self.client, url, {"emoji": "🧨"})
        self.assertEqual(invalid.status_code, 400)

        outsider = Client()
        outsider.force_login(self.carol)
        self.assertEqual(self.post_json(outsider, url, {"emoji": "❤️"}).status_code, 404)

    def test_read_cursor_updates_unread_count_and_cannot_move_backwards(self):
        first = Message.objects.create(
            conversation=self.conversation,
            sender=self.bob,
            content="first",
        )
        second = Message.objects.create(
            conversation=self.conversation,
            sender=self.bob,
            content="second",
        )
        read_url = f"/api/conversations/{self.conversation.pk}/read/"
        rows = self.client.get("/api/conversations/").json()["conversations"]
        row = next(item for item in rows if item["id"] == self.conversation.pk)
        self.assertEqual(row["unread_count"], 2)
        result = self.post_json(self.client, read_url, {"message_id": second.pk})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["conversation"]["unread_count"], 0)
        state = self.conversation.read_states.get(user=self.alice)
        self.assertEqual(state.last_read_message_id, second.pk)
        self.post_json(self.client, read_url, {"message_id": first.pk})
        state.refresh_from_db()
        self.assertEqual(state.last_read_message_id, second.pk)
        self.assertEqual(self.post_json(self.client, read_url, {"message_id": 99999}).status_code, 404)

    def test_read_cursor_requires_membership_authentication_and_csrf(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.bob,
            content="private",
        )
        url = f"/api/conversations/{self.conversation.pk}/read/"
        payload = json.dumps({"message_id": message.pk})
        anonymous = Client()
        outsider = Client()
        outsider.force_login(self.carol)
        self.assertEqual(anonymous.post(url, data=payload, content_type="application/json").status_code, 401)
        self.assertEqual(outsider.post(url, data=payload, content_type="application/json").status_code, 404)

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.alice)
        self.assertEqual(csrf_client.post(url, data=payload, content_type="application/json").status_code, 403)
        token = csrf_client.get("/api/accounts/csrf/").json()["csrfToken"]
        allowed = csrf_client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(allowed.status_code, 200)


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


class WebSocketMessengerTests(TransactionTestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="password")
        self.bob = User.objects.create_user("bob", password="password")
        self.carol = User.objects.create_user("carol", password="password")
        self.conversation = self.create_conversation(self.alice, self.bob)
        self.other_conversation = self.create_conversation(self.alice, self.carol)

    @staticmethod
    def create_conversation(first, second):
        member_one, member_two = sorted((first, second), key=lambda user: user.pk)
        return Conversation.objects.create(member_one=member_one, member_two=member_two)

    @staticmethod
    def authenticated_client_and_socket(
        user,
        conversation_id,
        origin="http://localhost:3000",
    ):
        client = Client()
        client.force_login(user)
        session_cookie = client.cookies[settings.SESSION_COOKIE_NAME].value
        headers = [
            (b"origin", origin.encode()),
            (b"cookie", f"{settings.SESSION_COOKIE_NAME}={session_cookie}".encode()),
        ]
        socket = WebsocketCommunicator(
            application,
            f"/ws/conversations/{conversation_id}/",
            headers=headers,
        )
        return client, socket

    def test_websocket_requires_login_and_allowed_origin(self):
        async_to_sync(self._test_websocket_rejections)()

    async def _test_websocket_rejections(self):
        anonymous = WebsocketCommunicator(
            application,
            f"/ws/conversations/{self.conversation.pk}/",
            headers=[(b"origin", b"http://localhost:3000")],
        )
        connected, close_code = await anonymous.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4401)

        _, invalid_origin = await sync_to_async(
            self.authenticated_client_and_socket,
            thread_sensitive=True,
        )(
            self.alice,
            self.conversation.pk,
            origin="https://attacker.example",
        )
        connected, _ = await invalid_origin.connect()
        self.assertFalse(connected)

    def test_non_member_cannot_subscribe_to_conversation(self):
        async_to_sync(self._test_non_member_rejection)()

    async def _test_non_member_rejection(self):
        _, socket = await sync_to_async(
            self.authenticated_client_and_socket,
            thread_sensitive=True,
        )(self.carol, self.conversation.pk)
        connected, close_code = await socket.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4404)

    def test_messages_reach_only_participants_and_persist(self):
        async_to_sync(self._test_message_delivery)()

    def test_message_edits_reactions_and_tombstones_sync_only_to_the_conversation(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.alice,
            content="private original text",
        )
        client = Client()
        client.force_login(self.alice)
        async_to_sync(self._test_message_operations_delivery)(message.pk, client)

    async def _test_message_operations_delivery(self, message_id, client):
        create_socket = sync_to_async(
            self.authenticated_client_and_socket,
            thread_sensitive=True,
        )
        _, alice_socket = await create_socket(self.alice, self.conversation.pk)
        _, bob_socket = await create_socket(self.bob, self.conversation.pk)
        _, carol_socket = await create_socket(self.carol, self.other_conversation.pk)
        for socket in (alice_socket, bob_socket, carol_socket):
            connected, _ = await socket.connect()
            self.assertTrue(connected)

        message_url = f"/api/conversations/{self.conversation.pk}/messages/{message_id}/"
        edited = await sync_to_async(client.patch, thread_sensitive=True)(
            message_url,
            data=json.dumps({"content": "edited private text"}),
            content_type="application/json",
        )
        self.assertEqual(edited.status_code, 200)
        for socket in (alice_socket, bob_socket):
            event = await socket.receive_json_from()
            self.assertEqual(event["type"], "message.updated")
            self.assertEqual(event["message"]["content"], "edited private text")
        self.assertTrue(await carol_socket.receive_nothing(timeout=0.05))

        reacted = await sync_to_async(client.post, thread_sensitive=True)(
            f"{message_url}reactions/",
            data=json.dumps({"emoji": "👍"}),
            content_type="application/json",
        )
        self.assertEqual(reacted.status_code, 200)
        alice_event = await alice_socket.receive_json_from()
        bob_event = await bob_socket.receive_json_from()
        self.assertEqual(alice_event["type"], "message.updated")
        self.assertTrue(alice_event["message"]["reactions"][0]["reacted"])
        self.assertFalse(bob_event["message"]["reactions"][0]["reacted"])
        self.assertTrue(await carol_socket.receive_nothing(timeout=0.05))

        deleted = await sync_to_async(client.delete, thread_sensitive=True)(message_url)
        self.assertEqual(deleted.status_code, 200)
        for socket in (alice_socket, bob_socket):
            event = await socket.receive_json_from()
            self.assertEqual(event["type"], "message.updated")
            self.assertEqual(event["message"]["content"], "")
            self.assertIsNotNone(event["message"]["deleted_at"])
            self.assertNotIn("edited private text", json.dumps(event["message"]))
        self.assertTrue(await carol_socket.receive_nothing(timeout=0.05))
        for socket in (alice_socket, bob_socket, carol_socket):
            await socket.disconnect()

    async def _test_message_delivery(self):
        create_socket = sync_to_async(
            self.authenticated_client_and_socket,
            thread_sensitive=True,
        )
        _, alice_socket = await create_socket(self.alice, self.conversation.pk)
        _, bob_socket = await create_socket(self.bob, self.conversation.pk)
        _, carol_socket = await create_socket(
            self.carol,
            self.other_conversation.pk,
        )
        for socket in (alice_socket, bob_socket, carol_socket):
            connected, _ = await socket.connect()
            self.assertTrue(connected)

        response = await sync_to_async(
            self.client_post_message,
            thread_sensitive=True,
        )()
        self.assertEqual(response.status_code, 201)
        persisted_id = response.json()["message"]["id"]

        alice_event = await alice_socket.receive_json_from()
        bob_event = await bob_socket.receive_json_from()
        self.assertEqual(alice_event["type"], "message.created")
        self.assertEqual(alice_event["message"]["id"], persisted_id)
        self.assertEqual(bob_event, alice_event)
        self.assertTrue(await carol_socket.receive_nothing(timeout=0.05))

        await bob_socket.disconnect()
        second_response = await sync_to_async(
            self.client_post_message,
            thread_sensitive=True,
        )()
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(
            (await alice_socket.receive_json_from())["message"]["id"],
            second_response.json()["message"]["id"],
        )
        self.assertTrue(await carol_socket.receive_nothing(timeout=0.05))
        self.assertEqual(await sync_to_async(Message.objects.count, thread_sensitive=True)(), 2)
        await alice_socket.disconnect()
        await carol_socket.disconnect()

    def client_post_message(self):
        client = Client()
        client.force_login(self.alice)
        return client.post(
            f"/api/conversations/{self.conversation.pk}/messages/",
            data=json.dumps({"content": "realtime"}),
            content_type="application/json",
        )

    def test_logout_invalidates_an_open_socket_on_heartbeat(self):
        async_to_sync(self._test_session_revalidation)()

    def test_typing_events_are_temporary_and_limited_to_current_conversation(self):
        async_to_sync(self._test_typing_events)()

    def test_read_cursor_reaches_the_other_conversation_member(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.alice,
            content="read receipt target",
        )
        async_to_sync(self._test_read_delivery)(message.pk)

    async def _test_read_delivery(self, message_id):
        create_socket = sync_to_async(
            self.authenticated_client_and_socket,
            thread_sensitive=True,
        )
        _, bob_socket = await create_socket(self.bob, self.conversation.pk)
        connected, _ = await bob_socket.connect()
        self.assertTrue(connected)
        response = await sync_to_async(self.client_mark_read, thread_sensitive=True)(message_id)
        self.assertEqual(response.status_code, 200)
        event = await bob_socket.receive_json_from()
        self.assertEqual(event["type"], "conversation.read")
        self.assertEqual(event["message_id"], message_id)
        await bob_socket.disconnect()

    def client_mark_read(self, message_id):
        client = Client()
        client.force_login(self.alice)
        return client.post(
            f"/api/conversations/{self.conversation.pk}/read/",
            data=json.dumps({"message_id": message_id}),
            content_type="application/json",
        )

    async def _test_typing_events(self):
        create_socket = sync_to_async(
            self.authenticated_client_and_socket,
            thread_sensitive=True,
        )
        _, alice_socket = await create_socket(self.alice, self.conversation.pk)
        _, bob_socket = await create_socket(self.bob, self.conversation.pk)
        _, carol_socket = await create_socket(self.carol, self.other_conversation.pk)
        for socket in (alice_socket, bob_socket, carol_socket):
            connected, _ = await socket.connect()
            self.assertTrue(connected)

        await alice_socket.send_json_to({"type": "typing", "is_typing": True})
        typing_event = await bob_socket.receive_json_from()
        self.assertEqual(typing_event["type"], "typing.changed")
        self.assertEqual(typing_event["user_id"], self.alice.pk)
        self.assertTrue(typing_event["is_typing"])
        self.assertTrue(await alice_socket.receive_nothing(timeout=0.05))
        self.assertTrue(await carol_socket.receive_nothing(timeout=0.05))

        await alice_socket.send_json_to({"type": "typing", "is_typing": False})
        stopped_event = await bob_socket.receive_json_from()
        self.assertFalse(stopped_event["is_typing"])
        for socket in (alice_socket, bob_socket, carol_socket):
            await socket.disconnect()

    async def _test_session_revalidation(self):
        client, socket = await sync_to_async(
            self.authenticated_client_and_socket,
            thread_sensitive=True,
        )(self.alice, self.conversation.pk)
        connected, _ = await socket.connect()
        self.assertTrue(connected)

        await sync_to_async(client.logout, thread_sensitive=True)()
        with patch("messaging.consumers.SESSION_RECHECK_SECONDS", 0):
            await socket.send_json_to({"type": "ping"})
            close_event = await socket.receive_output()
        self.assertEqual(close_event["type"], "websocket.close")
        self.assertEqual(close_event["code"], 4401)
