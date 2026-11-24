from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from openai import OpenAI

from app.bot.discord_utils import safe_defer, safe_followup_send
from app.shopping.ai import audio_to_items, sort_items

if TYPE_CHECKING:
    from app.shopping.store import ShoppingStore


logger = logging.getLogger(__name__)
MAX_AUDIO_BYTES = 25_000_000
AUDIO_EXTENSIONS = {
    ".flac", ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".ogg", ".wav", ".webm",
}


def register_shopping_commands(
    bot: commands.Bot,
    store: ShoppingStore,
    openai_client: OpenAI,
    channel_id: int,
) -> None:
    @bot.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot or message.channel.id != channel_id:
            return
        if message.content.startswith(("!", "[ ! ]")):
            return

        audio_attachments = [
            attachment
            for attachment in message.attachments
            if attachment.is_voice_message()
            or (attachment.content_type or "").startswith("audio/")
            or Path(attachment.filename).suffix.lower() in AUDIO_EXTENSIONS
        ]
        if audio_attachments:
            await add_audio_items(message, audio_attachments)
            return

        items = [item.strip() for item in message.content.splitlines() if item.strip()]
        if not items:
            return
        list_id = await asyncio.to_thread(store.add_items, items)
        for item in items:
            logger.info("Added %s to shopping list %s", item, list_id)

    async def add_audio_items(
        message: discord.Message, attachments: list[discord.Attachment]
    ) -> None:
        for attachment in attachments:
            if Path(attachment.filename).suffix.lower() not in AUDIO_EXTENSIONS:
                await message.reply(
                    "[ ! ] Formato de áudio não suportado. Envie OGG, MP3, MP4, "
                    "MPEG, MPGA, M4A, WAV, WEBM ou FLAC.",
                    mention_author=False,
                )
                return
            if attachment.size > MAX_AUDIO_BYTES:
                await message.reply(
                    "[ ! ] Cada áudio deve ter no máximo 25 MB.", mention_author=False
                )
                return

        try:
            items = []
            for attachment in attachments:
                audio = await attachment.read()
                if len(audio) > MAX_AUDIO_BYTES:
                    raise ValueError("Audio exceeds upload limit")
                items.extend(
                    await audio_to_items(openai_client, attachment.filename, audio)
                )
        except Exception:
            logger.exception("Failed to process shopping audio for message %s", message.id)
            await message.reply(
                "[ ! ] Não consegui processar o áudio. Nenhum item foi adicionado. "
                "Tente novamente ou envie os itens por texto.",
                mention_author=False,
            )
            return

        if not items:
            await message.reply(
                "[ ! ] Não identifiquei itens para adicionar no áudio. "
                "Diga quais produtos você quer colocar na lista da feira.",
                mention_author=False,
            )
            return

        try:
            list_id = await asyncio.to_thread(store.add_items, items)
        except Exception:
            logger.exception("Failed to save shopping audio for message %s", message.id)
            await message.reply(
                "[ ! ] Não consegui confirmar a gravação dos itens. "
                "Confira /lista antes de reenviar para evitar duplicação.",
                mention_author=False,
            )
            return

        logger.info("Added %s audio items to shopping list %s", len(items), list_id)
        formatted_items = "\n".join(f"- {item}" for item in items)
        if len(formatted_items) > 1800:
            formatted_items = (
                formatted_items[:1800] + "\n… Use /lista para ver todos os itens."
            )
        await message.reply(
            f"[ ! ] Itens adicionados à lista da feira: {len(items)}\n{formatted_items}",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @bot.tree.command(name="lista", description="Shows the current shopping list.")
    async def lista_command(interaction: discord.Interaction) -> None:
        shopping_list = await asyncio.to_thread(store.get_current_list)
        if not shopping_list.items:
            await interaction.response.send_message(
                f"[ ! ] Shopping list {shopping_list.list_id} is currently empty."
            )
            return

        formatted_list = "\n".join(f"- {item}" for item in shopping_list.items)
        chunks = [
            formatted_list[start : start + 1800]
            for start in range(0, len(formatted_list), 1800)
        ]
        await interaction.response.send_message(
            f"[ ! ] Shopping List (list_id: {shopping_list.list_id}):\n```\n"
            f"{chunks[0]}\n```",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        for chunk in chunks[1:]:
            await interaction.followup.send(
                f"```\n{chunk}\n```", allowed_mentions=discord.AllowedMentions.none()
            )

    @bot.tree.command(
        name="ordenar", description="Organizes the shopping list using GPT-4."
    )
    async def ordenar_command(interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return

        shopping_list = await asyncio.to_thread(store.get_current_list)
        if not shopping_list.items:
            await safe_followup_send(
                interaction,
                f"[ ! ] Shopping list {shopping_list.list_id} is currently empty.",
            )
            return

        try:
            sorted_list = await sort_items(openai_client, list(shopping_list.items))
        except Exception:
            logger.exception("Failed to sort shopping list %s", shopping_list.list_id)
            await safe_followup_send(
                interaction, "[ ! ] An error occurred while sorting the list."
            )
            return

        await safe_followup_send(
            interaction,
            f"[ ! ] Sorted Shopping List (list_id: {shopping_list.list_id}):\n```\n"
            f"{sorted_list}\n```",
        )
