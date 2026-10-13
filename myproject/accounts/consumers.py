from urllib.parse import parse_qs
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.db.models import Q

from .models import ChatMessage, Alumni


class AccountConsumer(AsyncJsonWebsocketConsumer):
    """Handle live WhatsApp chat events for alumni in the directory."""

    async def connect(self):
        query_string = self.scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        alumni_id_param = None
        if "alumni_id" in params and params["alumni_id"][0].isdigit():
            alumni_id_param = int(params["alumni_id"][0])

        session_alumni_id = self.scope.get("session", {}).get("alumni_id")
        self.alumni_id = alumni_id_param or session_alumni_id

        if not self.alumni_id:
            self.alumni_id = await self.get_default_alumni_id()

        if not self.alumni_id:
            await self.close(code=4001)
            return

        self.group_name = f"alumni_{self.alumni_id}"

        if self.channel_layer:
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name,
            )

        await self.accept()
        await self.send_json(
            {
                "type": "connection",
                "status": "connected",
                "alumni_id": self.alumni_id,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name") and self.group_name and self.channel_layer:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive_json(self, content, **kwargs):
        try:
            message_type = content.get("type") if isinstance(content, dict) else None

            if message_type == "ping":
                await self.send_json({"type": "pong"})
                return

            if message_type == "message":
                await self.send_message(content)
                return

            if message_type == "history":
                await self.send_history(content)
                return

            if message_type == "recent":
                await self.send_recent_conversations()
                return

            await self.send_json(
                {
                    "type": "error",
                    "message": "Unsupported message type.",
                }
            )
        except Exception as e:
            await self.send_json(
                {
                    "type": "error",
                    "message": f"Server error: {str(e)}",
                }
            )

    async def account_notification(self, event):
        await self.send_json(
            {
                "type": "notification",
                "message": event.get("message", "You have a new account notification."),
            }
        )

    async def chat_message(self, event):
        await self.send_json(event["payload"])

    async def send_history(self, content):
        recipient_id = content.get("recipient_id")
        if not str(recipient_id).isdigit() or int(recipient_id) == self.alumni_id:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Choose a valid alumni to view this conversation.",
                }
            )
            return

        messages = await self.get_history(int(recipient_id))
        await self.send_json(
            {
                "type": "history",
                "recipient_id": int(recipient_id),
                "messages": messages,
            }
        )

    async def send_recent_conversations(self):
        recent = await self.get_recent_conversations()
        await self.send_json(
            {
                "type": "recent",
                "conversations": recent,
            }
        )

    async def send_message(self, content):
        recipient_id = content.get("recipient_id")
        message = str(content.get("message", "")).strip()

        if not str(recipient_id).isdigit() or not message:
            await self.send_json(
                {
                    "type": "error",
                    "message": "recipient_id and message are required.",
                }
            )
            return

        recipient_id = int(recipient_id)
        if recipient_id == self.alumni_id or len(message) > 2000:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Choose another alumni and use a message up to 2000 characters.",
                }
            )
            return

        saved_message = await self.save_message(
            recipient_id,
            message,
        )
        payload = {
            "type": "message",
            "id": saved_message["id"],
            "sender_id": self.alumni_id,
            "sender_name": saved_message["sender_name"],
            "recipient_id": recipient_id,
            "message": message,
            "created_at": saved_message["created_at"],
            "time_str": saved_message["time_str"],
        }

        if self.channel_layer:
            await self.channel_layer.group_send(
                f"alumni_{recipient_id}",
                {
                    "type": "chat_message",
                    "payload": {**payload, "status": "received"},
                },
            )
        await self.send_json({**payload, "status": "sent"})

    @database_sync_to_async
    def get_default_alumni_id(self):
        first = Alumni.objects.first()
        return first.id if first else None

    @database_sync_to_async
    def save_message(self, recipient_id, message):
        saved_message = ChatMessage.objects.create(
            sender_id=self.alumni_id,
            recipient_id=recipient_id,
            message=message,
        )
        sender = Alumni.objects.filter(id=self.alumni_id).first()
        sender_name = sender.full_name if sender else f"Alumni #{self.alumni_id}"
        return {
            "id": saved_message.id,
            "sender_name": sender_name,
            "created_at": saved_message.created_at.isoformat(),
            "time_str": saved_message.created_at.strftime("%I:%M %p"),
        }

    @database_sync_to_async
    def get_history(self, recipient_id):
        conversation = ChatMessage.objects.filter(
            Q(sender_id=self.alumni_id, recipient_id=recipient_id)
            | Q(sender_id=recipient_id, recipient_id=self.alumni_id)
        ).order_by("created_at")[:200]

        sender_ids = {m.sender_id for m in conversation}
        senders = {a.id: a.full_name for a in Alumni.objects.filter(id__in=sender_ids)}

        return [
            {
                "id": message.id,
                "sender_id": message.sender_id,
                "sender_name": senders.get(message.sender_id, f"Alumni #{message.sender_id}"),
                "recipient_id": message.recipient_id,
                "message": message.message,
                "created_at": message.created_at.isoformat(),
                "time_str": message.created_at.strftime("%I:%M %p"),
            }
            for message in conversation
        ]

    @database_sync_to_async
    def get_recent_conversations(self):
        messages = ChatMessage.objects.filter(
            Q(sender_id=self.alumni_id) | Q(recipient_id=self.alumni_id)
        ).order_by("-created_at")[:300]

        conversations = {}
        for m in messages:
            other_id = m.recipient_id if m.sender_id == self.alumni_id else m.sender_id
            if other_id not in conversations:
                conversations[other_id] = {
                    "other_id": other_id,
                    "last_message": m.message,
                    "created_at": m.created_at.isoformat(),
                    "time_str": m.created_at.strftime("%I:%M %p"),
                    "unread_count": 0,
                }
            if m.recipient_id == self.alumni_id:
                conversations[other_id]["unread_count"] += 1

        return list(conversations.values())

