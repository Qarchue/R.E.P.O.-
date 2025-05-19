import sqlalchemy
import asyncio
from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .group_manager import GroupManager
import discord
from discord.ui import Select, View
from discord.ext import commands

from datetime import datetime

from utility import config, LOG, EmbedTemplate

from database import (
    Database, WhiteList, BlackList, ServerConfiguration, Server, 
    UserConfiguration, User, UserRecord, Group
)

class PermissionManager:


    async def _default_overwrites(
        guild: discord.Guild,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
    ) -> None:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
            send_messages=True, 
            view_channel=True, 
            connect=True
            ),
            user: discord.PermissionOverwrite(
            manage_channels=True,
            move_members=True,
            ),
        }

        await voice_channel.edit(overwrites=overwrites)

    async def _whitelist(
        guild: discord.Guild,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
        user_list: List[WhiteList],
    ) -> None:
        whitelist = user_list
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
            send_messages=True, 
            view_channel=True, 
            connect=True
            ),
            user: discord.PermissionOverwrite(
            manage_channels=True,
            move_members=True,
            ),
        }
        for white in whitelist:
            white_user = guild.get_member(white.discord_id)
            if white_user:
                overwrites[white_user] = discord.PermissionOverwrite(view_channel=True, connect=True)
        await voice_channel.edit(overwrites=overwrites)
    
    async def _blacklist(
        guild: discord.Guild,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
        user_list: List[BlackList],
    ) -> None:
        blacklist = user_list
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
            send_messages=True, 
            view_channel=True, 
            connect=True
            ),
            user: discord.PermissionOverwrite(
            manage_channels=True,
            move_members=True,
            ),
        }
        for black in blacklist:
            black_user = guild.get_member(black.discord_id)
            if black_user:
                overwrites[black_user] = discord.PermissionOverwrite(view_channel=True, connect=False)
        await voice_channel.edit(overwrites=overwrites)

    async def _password(
        guild: discord.Guild,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
    ) -> None:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
            send_messages=True, 
            view_channel=True, 
            connect=True
            ),
            user: discord.PermissionOverwrite(
            manage_channels=True,
            move_members=True,
            ),
        }
        await voice_channel.edit(overwrites=overwrites)


    async def change_limit(
        guild: discord.Guild,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
        white_list: List[WhiteList],
        black_list: List[BlackList],
        limit_mode: int,
    ):
        """
        更改權限
        """
        if limit_mode == 0:
            # 預設模式
            await PermissionManager._default_overwrites(guild, user, voice_channel)
        elif limit_mode == 1:
            # 白名單模式
            await PermissionManager._whitelist(guild, user, voice_channel, white_list)
        elif limit_mode == 2:
            # 黑名單模式
            await PermissionManager._blacklist(guild, user, voice_channel, black_list)
        elif limit_mode == 3:
            # 密碼模式
            await PermissionManager._password(guild, user, voice_channel)






    @staticmethod
    def _white_list_check(
        user_id: int,
        white_list: List[WhiteList],
    ) -> bool:
        return  user_id in [user.discord_id for user in white_list]

    @staticmethod
    def _black_list_check(
        user_id: int,
        black_list: List[BlackList],
    ) -> bool:
        return user_id in [user.discord_id for user in black_list]
    
    @staticmethod
    def _password_check(
        password: str,
        input_password: str,
    ) -> bool:
        return input_password == password
    

    @staticmethod
    async def check_join_permission(
        interaction: discord.Interaction,
        limit_mode: int,
        voice_channel: discord.VoiceChannel,
        parent: 'GroupManager',
        white_list: Optional[List[WhiteList]] = None,
        black_list: Optional[List[BlackList]] = None,
        password: Optional[str] = None,
    ) -> bool:
        """
        檢查用戶是否有權限加入語音頻道
        """
        LOG.Debug(f"cjp")
        user_id = interaction.user.id
        if limit_mode == 0:
            await parent._handle_permission_check(
                interaction=interaction,
                user=interaction.user,
                voice_channel=voice_channel,
                limit_mode=limit_mode,
                move=True
            )
        elif limit_mode == 1:
            await parent._handle_permission_check(
                interaction=interaction,
                user=interaction.user,
                voice_channel=voice_channel,
                limit_mode=limit_mode,
                move=PermissionManager._white_list_check(user_id, white_list)
            )
        elif limit_mode == 2:
            await parent._handle_permission_check(
                interaction=interaction,
                user=interaction.user,
                voice_channel=voice_channel,
                limit_mode=limit_mode,
                move=not PermissionManager._black_list_check(user_id, black_list)
            )
        elif limit_mode == 3:
            # 密碼模式
            await interaction.response.send_modal(
                parent.enter_password(
                    parent=parent,
                    voice_channel=voice_channel,
                    password=password,
                    callback=PermissionManager._handle_enter_password,
                )
            )
            # PermissionManager._password_check(password, input_password)
    

    @staticmethod
    async def _handle_enter_password(
        interaction: discord.Interaction,
        parent: 'GroupManager',
        voice_channel: discord.VoiceChannel,
        password: str,
        input_password: str,
    ) -> None:
        await parent._handle_permission_check(
            interaction=interaction,
            user=interaction.user,
            voice_channel=voice_channel,
            limit_mode=3,
            move=PermissionManager._password_check(password, input_password)
        )