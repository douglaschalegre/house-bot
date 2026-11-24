"""Partial integration: real SDK and SQLite; Discord and OpenAI HTTP are mocked."""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import discord
import httpx
from discord.ext import commands
from openai import OpenAI

from app.bot.shopping_commands import MAX_AUDIO_BYTES, register_shopping_commands
from app.database import Database
from app.shopping.store import ShoppingStore


def completion(items, *, finish_reason="stop", refusal=None):
    return {
        "id": "chat-test",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-mini",
        "choices": [{
            "index": 0,
            "finish_reason": finish_reason,
            "message": {
                "role": "assistant",
                "content": json.dumps({"items": items}),
                "refusal": refusal,
            },
        }],
    }


def attachment(filename="voice.ogg", *, content_type="audio/ogg", size=10):
    return SimpleNamespace(
        filename=filename,
        content_type=content_type,
        size=size,
        is_voice_message=lambda: filename == "voice.ogg",
        read=AsyncMock(return_value=b"OggS-test-audio"),
    )


class ShoppingAudioTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = Database(f"sqlite:///{Path(self.tmp.name) / 'shopping.db'}")
        self.store = ShoppingStore(self.database)
        self.requests = []
        self.responses = []

        def handle(request):
            self.requests.append(request)
            status, body = self.responses.pop(0)
            return httpx.Response(status, json=body)

        self.client = OpenAI(
            api_key="test-key",
            http_client=httpx.Client(transport=httpx.MockTransport(handle)),
        )
        self.bot = commands.Bot(command_prefix="!", intents=discord.Intents.none())
        register_shopping_commands(self.bot, self.store, self.client, channel_id=42)
        self.message = SimpleNamespace(
            id=100,
            author=SimpleNamespace(bot=False),
            channel=SimpleNamespace(id=42),
            content="",
            attachments=[attachment()],
            reply=AsyncMock(),
        )

    async def asyncTearDown(self):
        await self.bot.close()
        self.client.close()
        self.database.engine.dispose()
        self.tmp.cleanup()

    async def test_transcribes_interprets_and_commits_before_reply(self):
        transcript = "Coloca dois quilos de tomate e seis bananas. Leite não, já temos."
        items = ["2 kg de tomate", "6 bananas"]
        self.responses = [(200, {"text": transcript}), (200, completion(items))]
        self.message.content = "Segue o áudio"

        async def check_committed(*args, **kwargs):
            self.assertEqual(self.store.list_current_items(), items)

        self.message.reply.side_effect = check_committed
        await self.bot.on_message(self.message)

        self.assertEqual(len(self.requests), 2)
        upload, interpretation = self.requests
        self.assertEqual(upload.url.path, "/v1/audio/transcriptions")
        self.assertIn(b"gpt-transcribe", upload.content)
        self.assertIn(b'filename="voice.ogg"', upload.content)
        self.assertIn(b"OggS-test-audio", upload.content)
        self.assertIn(b'languages', upload.content)
        self.assertIn(b'pt', upload.content)
        body = json.loads(interpretation.content)
        self.assertEqual(body["model"], "gpt-4o-mini")
        self.assertEqual(body["messages"][1]["content"], transcript)
        self.assertTrue(body["response_format"]["json_schema"]["strict"])
        self.message.reply.assert_awaited_once()
        self.assertIn("2 kg de tomate", self.message.reply.call_args.args[0])
        self.assertFalse(self.message.reply.call_args.kwargs["allowed_mentions"].everyone)

    async def test_multiple_files_write_once_after_all_interpretations(self):
        self.message.attachments.append(attachment("shopping.mp3", content_type=None))
        self.responses = [
            (200, {"text": "arroz"}), (200, completion(["arroz"])),
            (200, {"text": "feijão"}), (200, completion(["feijão"])),
        ]
        with patch.object(self.store, "add_items", wraps=self.store.add_items) as add:
            await self.bot.on_message(self.message)
        add.assert_called_once_with(["arroz", "feijão"])
        self.assertEqual(self.store.list_current_items(), ["arroz", "feijão"])

    async def test_later_audio_failure_does_not_persist_earlier_items(self):
        self.message.attachments.append(attachment("second.ogg"))
        self.responses = [
            (200, {"text": "arroz"}), (200, completion(["arroz"])),
            (503, {"error": {"message": "Unavailable"}}),
        ]
        with self.assertLogs("app.bot.shopping_commands", level="ERROR"):
            await self.bot.on_message(self.message)
        self.assertEqual(len(self.requests), 3)
        self.assertEqual(self.store.list_current_items(), [])
        self.assertIn("Nenhum item", self.message.reply.call_args.args[0])

    async def test_no_speech_or_no_addition_does_not_write(self):
        for responses in (
            [(200, {"text": "  "})],
            [(200, {"text": "Apaga a lista"}), (200, completion([]))],
        ):
            with self.subTest(responses=responses):
                self.responses = responses
                with patch.object(self.store, "add_items") as add:
                    await self.bot.on_message(self.message)
                add.assert_not_called()
                self.assertIn("Não identifiquei", self.message.reply.call_args.args[0])

    async def test_invalid_incomplete_and_refused_interpretations_do_not_write(self):
        for body in (
            completion(["arroz"], finish_reason="length"),
            completion([], refusal="Cannot process"),
            completion(["arroz", 3]),
            completion(["  "]),
            completion(["x" * 201]),
            completion(["arroz"] * 51),
            completion("arroz"),
        ):
            with self.subTest(body=body):
                self.responses = [(200, {"text": "arroz"}), (200, body)]
                with (
                    patch.object(self.store, "add_items") as add,
                    self.assertLogs("app.bot.shopping_commands", level="ERROR"),
                ):
                    await self.bot.on_message(self.message)
                add.assert_not_called()

    async def test_invalid_attachments_rejected_before_download_or_openai(self):
        for invalid in (
            attachment(size=MAX_AUDIO_BYTES + 1),
            attachment("shopping.aac", content_type="audio/aac"),
        ):
            with self.subTest(filename=invalid.filename, size=invalid.size):
                first = attachment()
                self.message.attachments = [first, invalid]
                await self.bot.on_message(self.message)
                first.read.assert_not_awaited()
                invalid.read.assert_not_awaited()
        self.assertEqual(self.requests, [])

    async def test_download_failure_does_not_call_openai(self):
        self.message.attachments[0].read.side_effect = discord.HTTPException(
            SimpleNamespace(status=404, reason="Not Found"), "Deleted attachment"
        )
        with self.assertLogs("app.bot.shopping_commands", level="ERROR"):
            await self.bot.on_message(self.message)
        self.assertEqual(self.requests, [])
        self.assertIn("Nenhum item", self.message.reply.call_args.args[0])

    async def test_store_failure_asks_to_check_list_before_retry(self):
        self.responses = [(200, {"text": "arroz"}), (200, completion(["arroz"]))]
        with (
            patch.object(self.store, "add_items", side_effect=RuntimeError()),
            self.assertLogs("app.bot.shopping_commands", level="ERROR"),
        ):
            await self.bot.on_message(self.message)
        self.assertIn("Confira /lista", self.message.reply.call_args.args[0])

    async def test_long_confirmation_fits_discord_limit(self):
        items = [f"Produto {i} " + "x" * 170 for i in range(50)]
        self.responses = [(200, {"text": "compras"}), (200, completion(items))]
        await self.bot.on_message(self.message)
        self.assertEqual(self.store.list_current_items(), items)
        reply = self.message.reply.call_args.args[0]
        self.assertLessEqual(len(reply), 2000)
        self.assertIn("/lista", reply)

        interaction = SimpleNamespace(
            response=SimpleNamespace(send_message=AsyncMock()),
            followup=SimpleNamespace(send=AsyncMock()),
        )
        await self.bot.tree.get_command("lista").callback(interaction)
        replies = [interaction.response.send_message.call_args.args[0]]
        replies.extend(call.args[0] for call in interaction.followup.send.call_args_list)
        self.assertTrue(all(len(reply) <= 2000 for reply in replies))
        # Join code-block contents to prove no item was lost at a chunk boundary.
        rendered = "".join(reply.split("```\n", 1)[1].rsplit("\n```", 1)[0] for reply in replies)
        self.assertEqual(rendered, "\n".join(f"- {item}" for item in items))

    async def test_reply_failure_does_not_repeat_a_successful_write(self):
        self.responses = [(200, {"text": "arroz"}), (200, completion(["arroz"]))]
        self.message.reply.side_effect = discord.HTTPException(
            SimpleNamespace(status=403, reason="Forbidden"), "Missing permissions"
        )
        with patch.object(self.store, "add_items", wraps=self.store.add_items) as add:
            with self.assertRaises(discord.HTTPException):
                await self.bot.on_message(self.message)
        add.assert_called_once_with(["arroz"])
        self.assertEqual(self.store.list_current_items(), ["arroz"])

    async def test_malformed_json_and_payloads_do_not_write(self):
        for content in ('{', 'null', '[]', '{"items": [], "extra": true}'):
            with self.subTest(content=content):
                body = completion([])
                body["choices"][0]["message"]["content"] = content
                self.responses = [(200, {"text": "arroz"}), (200, body)]
                with (
                    patch.object(self.store, "add_items") as add,
                    self.assertLogs("app.bot.shopping_commands", level="ERROR"),
                ):
                    await self.bot.on_message(self.message)
                add.assert_not_called()

    async def test_text_and_filters_remain_compatible(self):
        self.message.attachments = [attachment("photo.png", content_type="image/png")]
        self.message.content = " arroz \n\n leite "
        await self.bot.on_message(self.message)
        self.assertEqual(self.store.list_current_items(), ["arroz", "leite"])
        self.message.reply.assert_not_awaited()

        self.message.attachments = [attachment()]
        for content, bot, channel in (
            ("!ignored", False, 42), ("[ ! ] ignored", False, 42),
            ("", True, 42), ("", False, 99),
        ):
            self.message.content = content
            self.message.author.bot = bot
            self.message.channel.id = channel
            await self.bot.on_message(self.message)
        self.message.attachments[0].read.assert_not_awaited()
        self.assertEqual(self.requests, [])


if __name__ == "__main__":
    unittest.main()
