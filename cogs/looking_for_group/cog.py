import sqlalchemy
import discord
import asyncio
from discord.ext import commands

from discord import app_commands

from database import Database, WhiteList, BlackList, ServerConfiguration, Server, UserConfiguration, User, Group, UserRecord, ServerTags

from utility import SlashCommandLogger, LOG, config, steam_API, TimeoutOperation

from typing import Optional, List

from managers.ui import CreateButtonView

from managers import GroupManager
from managers import SettingPasswordModal
from managers import SettingGroupModal
from managers.ui import ThreadMenuNav
from sqlalchemy.sql._typing import ColumnExpressionArgument
from asyncio import create_task, sleep


from functools import partial

class LookingForGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        # 用來追蹤語音頻道的倒數任務
        

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="設定揪團頻道", description="創建或設定揪團頻道，選項為可選")
    @app_commands.rename(
        category="揪團論壇所在類別",
        thread_name="揪團貼文標題",
        thread_content="揪團論壇描述",
        button_content="揪團按鈕訊息",
    )
    @SlashCommandLogger
    async def set_looking_for_group_channels(
        self,
        interaction: discord.Interaction, 
        category: Optional[discord.CategoryChannel] = None, 
        thread_name: Optional[str] = None, 
        thread_content: Optional[str] = None, 
        button_content: Optional[str] = None, 

    ):
        await interaction.response.defer(ephemeral=True)
        await GroupManager.ensure_channels(
            guild=interaction.guild,
            user=interaction.user,
            category=category,
            thread_name=thread_name,
            thread_content=thread_content,
            button_content=button_content,
        )

    async def cog_load(self):
        self.bot.add_view(CreateButtonView(GroupManager, SettingGroupModal))
        

        

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        guild = member.guild
        if before.channel is not None:
            await GroupManager.auto_delete_voice_channel(
                guild=guild,
                voice_channel=before.channel,
            )
        if after.channel is not None:
            await GroupManager.auto_delete_voice_channel(
                guild=guild,
                voice_channel=after.channel,
            )

    @app_commands.command(name="揪團密碼", description="設定密碼")
    @SlashCommandLogger
    async def set_group_password(
        self, interaction: discord.Interaction,
    ):
        user = interaction.user
        user_config = await Database.select_one(UserConfiguration, UserConfiguration.discord_id.is_(user.id))

        await interaction.response.send_modal(
            SettingPasswordModal(user_config=user_config)
        )

    @app_commands.command(name="揪團設定", description="揪團設定")
    @SlashCommandLogger
    async def group_setting(
        self, interaction: discord.Interaction,
    ):
        user = interaction.user
        user_config = await Database.select_one(UserConfiguration, UserConfiguration.discord_id.is_(user.id))
        user_record = await Database.select_one(UserRecord, UserRecord.discord_id.is_(user.id))

        await interaction.response.send_modal(
            SettingGroupModal(
                user_record=user_record,
                user_config=user_config,
                callback=GroupManager.update,
            )
        )
        
        

async def setup(client: commands.Bot):
    await client.add_cog(LookingForGroupCog(client))
