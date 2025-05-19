from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..group_manager import GroupManager

import discord
from discord.ui import View
from utility import LOG


class JoinButtonView(View):
    def __init__(
        self,
        owner: discord.Member,
        voice_channel: discord.VoiceChannel,
        group_manager: 'GroupManager',
    ):
        super().__init__(timeout=None)
        self.owner = owner
        self.voice_channel = voice_channel
        self.group_manager = group_manager

    @discord.ui.button(
        label="加入語音",
        style=discord.ButtonStyle.green,
        emoji="🚪",
        row=1,
        custom_id="group_ui:join_voice",
    )
    async def join_voice_button(self, interaction: discord.Interaction, button: discord.Button):
        LOG.Debug(f"加入語音按鈕被點擊: {interaction.user.name}")
        await self.group_manager.handle_join(interaction=interaction, voice_channel=self.voice_channel, owner=self.owner)



    async def update_button_state(self, interaction: discord.Interaction):
        pass
        # self.join_voice_button.disabled = (
        #     len(self.voice_channel.members) >= self.voice_channel.user_limit
        #     if self.voice_channel.user_limit > 0
        #     else False
        # )
        # self.join_voice_button.label = (
        #     "加入語音" if not self.join_voice_button.disabled else "語音已滿"
        # )
        

        # LOG.Debug(f"更新按鈕狀態: {self.join_voice_button.disabled}")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True
