import logging

import discord


logger = logging.getLogger(__name__)


async def safe_defer(interaction: discord.Interaction) -> bool:
    try:
        await interaction.response.defer(thinking=True)
        return True
    except discord.NotFound:
        logger.warning(
            "Interaction expired before defer for command %s",
            getattr(interaction.command, "name", "unknown"),
        )
        return False


async def safe_followup_send(
    interaction: discord.Interaction, message: str
) -> None:
    try:
        await interaction.followup.send(message)
    except discord.NotFound:
        logger.warning(
            "Interaction token expired before followup for command %s",
            getattr(interaction.command, "name", "unknown"),
        )

