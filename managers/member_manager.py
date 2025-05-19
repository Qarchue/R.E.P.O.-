import discord
from utility import LOG


class MemberManager:

    @staticmethod
    async def move_user_to_channel(
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
    ) -> None:
        try:
            await user.move_to(voice_channel)
            LOG.System(f"將使用者{LOG.User(user.id)}移動到頻道{voice_channel.name}")
        except Exception as e:
            LOG.Error(f"move_user_to_channel: {e}")

    @staticmethod
    async def check_user_in_voice_channel(
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
    ) -> bool:
        if user.voice and user.voice.channel == voice_channel:
            return True
        return False
    