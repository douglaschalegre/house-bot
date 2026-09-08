from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from openai import OpenAI

from app.bot.discord_utils import safe_defer, safe_followup_send
from app.shopping.ai import sort_items

if TYPE_CHECKING:
    from app.shopping.store import ShoppingStore


logger = logging.getLogger(__name__)


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

        items = [item.strip() for item in message.content.splitlines() if item.strip()]
        if not items:
            return
        list_id = await asyncio.to_thread(store.add_items, items)
        for item in items:
            logger.info("Added %s to shopping list %s", item, list_id)

    @bot.tree.command(name="lista", description="Shows the current shopping list.")
    async def lista_command(interaction: discord.Interaction) -> None:
        list_id, items = await asyncio.to_thread(store.get_current_list)
        if not items:
            await interaction.response.send_message(
                f"[ ! ] Shopping list {list_id} is currently empty."
            )
            return

        formatted_list = "\n".join(f"- {item}" for item in items)
        await interaction.response.send_message(
            f"[ ! ] Shopping List (list_id: {list_id}):\n```\n{formatted_list}\n```"
        )

    @bot.tree.command(
        name="ordenar", description="Organizes the shopping list using GPT-4."
    )
    async def ordenar_command(interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return

        list_id, items = await asyncio.to_thread(store.get_current_list)
        if not items:
            await safe_followup_send(
                interaction, f"[ ! ] Shopping list {list_id} is currently empty."
            )
            return

        try:
            sorted_list = await sort_items(openai_client, items)
        except Exception:
            logger.exception("Failed to sort shopping list %s", list_id)
            await safe_followup_send(
                interaction, "[ ! ] An error occurred while sorting the list."
            )
            return

        await safe_followup_send(
            interaction,
            f"[ ! ] Sorted Shopping List (list_id: {list_id}):\n```\n{sorted_list}\n```",
        )

