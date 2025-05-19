import discord

from database import WhiteList, BlackList

from typing import List

from utility import LOG
class VoiceChannelOperator:
    @staticmethod    
    async def create_voice_channel(
        guild: discord.Guild, 
        category: discord.CategoryChannel, 
        user_limit: int, 
        channel_name: str
    ) -> discord.VoiceChannel:
        
        return await guild.create_voice_channel(
            name=channel_name,
            category=category,
            user_limit=user_limit,
        )
    
    @staticmethod
    async def delete_voice_channel(
        voice_channel: discord.VoiceChannel
    ) -> None:
        if voice_channel is not None:
            await voice_channel.delete()

    async def update_voice_channel(
        voice_channel: discord.VoiceChannel,
        channel_name: str,
    ) -> None:
        if voice_channel is not None:
            await voice_channel.edit(
                name=channel_name,
            )

class VoiceChannelEnsurer:
    @staticmethod
    async def ensure_voice_channel(
        guild: discord.Guild,
        channel_id: int | None,
        category: discord.CategoryChannel,
        user_limit: int = 0,
    ) -> discord.VoiceChannel:
        voice_channel = None
        if channel_id is not None:
            channel = guild.get_channel(channel_id)
            if isinstance(channel, discord.VoiceChannel):
                voice_channel = channel
        if voice_channel is None:
            voice_channel = await VoiceChannelOperator.create_voice_channel(
                guild=guild,
                category=category,
                user_limit=user_limit,
                channel_name="揪團待機語音",
            )
            return voice_channel

        return voice_channel



class VoiceChannelManager(VoiceChannelOperator, VoiceChannelEnsurer):


    @staticmethod
    async def _default_overwrites(
        guild: discord.Guild,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
    ) -> None:
        try:
            await voice_channel.send(content="這個頻道的權限已經被重置")
        except Exception as e:
            LOG.System(f"發生錯誤vctxch: {e}")
        



    @staticmethod
    async def _whitelist(
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
        user_list: List[WhiteList],
    ) -> None:
        members = voice_channel.members
        discord_ids = [white_user.discord_id for white_user in user_list]

        for member in members:
            if member == user:
                continue
            if member.id not in discord_ids:
                await member.move_to(None)

    @staticmethod
    async def _blacklist(
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
        user_list: List[BlackList],
    ) -> None:
        members = voice_channel.members
        discord_ids = [black_user.discord_id for black_user in user_list]

        for member in members:
            if member == user:
                continue
            if member.id in discord_ids:
                await member.move_to(None)

    
    @staticmethod
    async def _password(
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
    ) -> None:
        members = voice_channel.members

        for member in members:
            if member == user:
                continue
            await member.move_to(None)


    @staticmethod
    async def change_limit(
        guild: discord.Guild,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
        white_list: List[WhiteList],
        black_list: List[BlackList],
        limit_mode: int,
    ) -> None:
        if limit_mode == 1:
            await VoiceChannelManager._whitelist(user, voice_channel, white_list)
        elif limit_mode == 2:
            await VoiceChannelManager._blacklist(user, voice_channel, black_list)
        elif limit_mode == 3:
            await VoiceChannelManager._password(user, voice_channel)


    @staticmethod
    def user_limit_check(
        voice_channel: discord.VoiceChannel,
    ) -> bool:
        if voice_channel.user_limit and len(voice_channel.members) >= voice_channel.user_limit:
            return True
        return False