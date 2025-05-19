import discord
from typing import Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from .group_manager import GroupManager
    from .ui.create_button import CreateButtonView
    from .ui.setting_group import SettingGroupModal
    from .ui.thread_menu import ThreadMenuNav
    from .ui.join_button import JoinButtonView

from discord.ext import commands
from database import UserConfiguration, UserRecord

class CreateButtonEnsure:
    @staticmethod
    async def ensure_create_button(
        thread: discord.Thread,
        button_message_id: int | None,
        button_content: str,
        view: 'CreateButtonView',
        group_manager: 'GroupManager',
        setting_group_modal: 'SettingGroupModal',
    ):
        button_message = None
        if button_message_id is not None:
            try:
                button_message = await thread.fetch_message(button_message_id)
            except:
                button_message = None
        if button_message is None:
            button_message = await thread.send(
                content=button_content,
                view=view(
                    group_manager=group_manager,
                    setting_group_modal=setting_group_modal,
                )
            )
            return button_message
        if button_message.content != button_content:
            await button_message.edit(
                content=button_content,
            )
        return button_message

class ViewManager(CreateButtonEnsure):

    @staticmethod
    async def add_join_button_view(
        bot: commands.Bot,
        join_button_view: 'JoinButtonView',
        owner: discord.Member,
        voice_channel: discord.VoiceChannel,
        group_manager: 'GroupManager',
    ) -> None:
        bot.add_view(
            join_button_view(
                owner=owner,
                voice_channel=voice_channel,
                group_manager=group_manager,
            )
        )

    
    @staticmethod
    async def add_thread_menu_view(
        bot: commands.Bot,
        thread_menu_view: 'ThreadMenuNav',
        guild: discord.Guild,
        user_config: UserConfiguration,
        user_record: UserRecord,
        group_manager: 'GroupManager',
        allowed_user: Optional[discord.Member] = None,
    ) -> None:
        bot.add_view(
            thread_menu_view(
                guild=guild,
                user_config=user_config,
                user_record=user_record,
                group_manager=group_manager,
                allowed_user=allowed_user
            )
        )

    
