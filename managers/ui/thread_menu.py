
from typing import List, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from ..group_manager import GroupManager
from functools import partial

import discord
from discord.ext import commands
from discord.ui import Select, View

from .setting_password import SettingPasswordModal

from .setting_group import SettingGroupModal

from .select_tags import TagSelect

from utility import config, LOG

from database import Database, WhiteList, BlackList, ServerConfiguration, Server, UserConfiguration, User, UserRecord, Group


class ThreadMenuNav(View):

    def __init__(
        self,
        guild: discord.Guild,
        user_config: UserConfiguration,
        user_record: UserRecord,
        group_manager: Optional['GroupManager'],
        allowed_user: Optional[discord.Member] = None,
    ):
        super().__init__(timeout=None)

        self.guild = guild
        self.user_config = user_config
        self.user_record = user_record
        self.allowed_user = allowed_user
        self.group_manager = group_manager
        self.update_button_states(user_config.limit_mode)

    def update_button_states(self, limit_mode: int):
        """Update the button states based on the limit mode."""
        self.update_button_disabled(limit_mode)
        self.update_button_color(limit_mode)

    def update_button_disabled(self, limit_mode: int):
        """Update the button disabled state."""
        self.no_list.disabled = limit_mode == 0
        self.white_list.disabled = limit_mode == 1
        self.black_list.disabled = limit_mode == 2
        self.password.disabled = limit_mode == 3

    def update_button_color(self, limit_mode: int):
        """Update the button color based on the limit mode."""
        self.no_list.style = discord.ButtonStyle.green if limit_mode == 0 else discord.ButtonStyle.gray
        self.white_list.style = discord.ButtonStyle.green if limit_mode == 1 else discord.ButtonStyle.gray
        self.black_list.style = discord.ButtonStyle.green if limit_mode == 2 else discord.ButtonStyle.gray
        self.password.style = discord.ButtonStyle.green if limit_mode == 3 else discord.ButtonStyle.gray

    async def update_ui(self, interaction: discord.Interaction, limit_mode: int):
        """Update the UI and change the limit mode."""
        self.update_button_states(limit_mode)
        await self.update(interaction)
        await self.group_manager.change_limit(
            interaction=interaction, limit_mode=limit_mode
        )

    @discord.ui.button(
        label="設定",
        style=discord.ButtonStyle.gray,
        emoji="⚙️",
        row=1,
        custom_id="group_ui:setting",
    )
    async def setting(self, interaction: discord.Interaction, button: discord.Button):
        try:
            modal = SettingGroupModal(
                user_record=self.user_record,
                user_config=self.user_config,
                callback=self.group_manager.update,
            )
            await interaction.response.send_modal(modal)

        except Exception as e:
            LOG.Error(f"密碼設定失敗: {e}")
            await interaction.followup.send("密碼設定失敗", ephemeral=True)

    @discord.ui.button(
        label="標籤",
        style=discord.ButtonStyle.gray,
        emoji="🏷️",
        row=1,
        custom_id="group_ui:tag",
        disabled=True,
    )
    async def tag(self, interaction: discord.Interaction, button: discord.Button):
        try:
            options=await self.group_manager.get_unknown_tags(
                    interaction=interaction,
            ),
            view = TagSelect(
                options=options,
                on_select=self.group_manager.update,
            )
            await interaction.response.send_message(
                view=view
            )
        except Exception as e:
            LOG.Error(f"標籤設定失敗: {e}")
    @discord.ui.button(
        label="降落",
        style=discord.ButtonStyle.gray,
        emoji="🪂",
        row=1,
        custom_id="group_ui:raid",
        disabled=True,
    )
    async def raid(self, interaction: discord.Interaction, button: discord.Button):
        pass

    @discord.ui.button(
        label="解散",
        style=discord.ButtonStyle.danger,
        emoji="💥",
        row=1,
        custom_id="group_ui:dissolution",
    )
    async def dissolution(self, interaction: discord.Interaction, button: discord.Button):
        try:
            await self.group_manager.delete(
                guild=self.guild,
                user_id=self.allowed_user.id,
                user_record=self.user_record,
                user_config=self.user_config,
            )
        except Exception as e:
            LOG.Error(f"解散房間失敗: {e}")
            await interaction.followup.send("解散房間失敗", ephemeral=True)
            return
            
    @discord.ui.button(
        label="無",
        style=discord.ButtonStyle.gray,
        emoji="🆓",
        row=2,
        custom_id="group_ui:no_list",
    )
    async def no_list(self, interaction: discord.Interaction, button: discord.Button):
        await self.update_ui(interaction, 0)

    @discord.ui.button(
        label="白名單",
        style=discord.ButtonStyle.gray,
        emoji="✅",
        row=2,
        custom_id="group_ui:white_list",
    )
    async def white_list(self, interaction: discord.Interaction, button: discord.Button):
        await self.update_ui(interaction, 1)

    @discord.ui.button(
        label="黑名單",
        style=discord.ButtonStyle.gray,
        emoji="⛔",
        row=2,
        custom_id="group_ui:black_list",
    )
    async def black_list(self, interaction: discord.Interaction, button: discord.Button):
        await self.update_ui(interaction, 2)

    @discord.ui.button(
        label="密碼",
        style=discord.ButtonStyle.gray,
        emoji="🔐",
        row=2,
        custom_id="group_ui:password",
    )
    async def password(self, interaction: discord.Interaction, button: discord.Button):
        try:
            modal = SettingPasswordModal(
                user_config=self.user_config, 
                callback=self.update_ui
            )
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            LOG.Error(f"密碼設定失敗: {e}")

    async def update(self, interaction: discord.Interaction):
        """Update the view in the interaction."""
        await interaction.response.edit_message(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if the interaction is from the allowed user."""
        return interaction.user == self.allowed_user

# class AppMenu():
#     """
#     Navigate pages using the Discord UI components.

#     This menu can be *partially* persistent with `client.add_view(AppMenu())`
#     This will allow the delete button to work on past messages

#     Args:
#         timeout (Optional[float], optional): The duration the interaction will be active for. Defaults to None.
#         ephemeral (Optional[bool], optional): Send as an ephemeral message. Defaults to False.
#     """

#     def __init__(
#         self,
#         timeout: Optional[float] = None,
#         ephemeral: Optional[bool] = False,
#     ) -> None:
#         # super().__init__()
#         self.timeout = timeout
#         self.ephemeral = ephemeral

#     async def send_pages(
#         self,
#         ctx: commands.Context,
#         destination: discord.abc.Messageable,
#         pages: List[discord.Embed],
#     ):
#         if ctx.interaction:
#             await ctx.interaction.response.send_message(
#                 embed=pages[0],
#                 view=AppNav(
#                     pages=pages,
#                     timeout=self.timeout,
#                     ephemeral=self.ephemeral,
#                     allowed_user=ctx.author,
#                 ),
#                 ephemeral=self.ephemeral,
#             )
#         else:
#             await destination.send(
#                 embed=pages[0],
#                 view=AppNav(pages=pages, timeout=self.timeout, allowed_user=ctx.author),
#             )




