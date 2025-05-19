from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from managers import GroupManager
    from managers.ui.setting_group import SettingGroupModal

import discord
from discord.ui import Select, View
import sqlalchemy
from datetime import datetime

from utility import config, LOG, EmbedTemplate




from database import Database, WhiteList, BlackList, ServerConfiguration, Server, UserConfiguration, User, UserRecord, Group


class CreateButtonView(discord.ui.View):
    def __init__(
        self, 
        group_manager: 'GroupManager', 
        setting_group_modal: 'SettingGroupModal',
        ):
        super().__init__(timeout=None)
        self.group_manager = group_manager
        self.setting_group_modal = setting_group_modal

    @discord.ui.button(
        label='創建揪團', 
        style=discord.ButtonStyle.green, 
        custom_id='persistent_view:green',
        emoji="➕"
    )
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user_record = await Database.select_one(UserRecord, UserRecord.discord_id.is_(interaction.user.id))
            user_config = await Database.select_one(UserConfiguration, UserConfiguration.discord_id.is_(interaction.user.id))
            group = await Database.select_one(Group, Group.owner_id.is_(interaction.user.id))
            if group is not None:
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal("你已經有一個揪團了，請先刪除舊的揪團。"), ephemeral=True
                )
                return
            modal = self.setting_group_modal(
                user_record=user_record, 
                user_config=user_config, 
                callback=self.group_manager.create
                )    
            await interaction.response.send_modal(modal)
        except Exception as e:
            LOG.Error(f"創建揪團按鈕失敗: {e}")

    async def modal_Complete(self, interaction: discord.Interaction):
        """
        當 modal 完成時的回調函數
        """
        
        await interaction.response.send_message(
            embed=EmbedTemplate.normal("創建中，請稍後..."), ephemeral=True
        )

