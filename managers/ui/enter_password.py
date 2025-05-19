import discord
from typing import Optional
from utility import LOG

class EnterPasswordModal(discord.ui.Modal, title="輸入密碼"):

    group_password: discord.ui.TextInput = discord.ui.TextInput(
        label="密碼",
        placeholder="請輸入房間密碼",  
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=30,
    )
    """設定密碼表單"""
    def __init__(self, parent, voice_channel: discord.VoiceChannel, password: str, callback: Optional[callable] = None):
        self.parent = parent
        self.voice_channel = voice_channel
        self.password = password
        self.callback = callback

        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback(
            interaction=interaction,
            parent=self.parent,
            voice_channel=self.voice_channel,
            password=self.password,
            input_password=self.group_password.value,
        )
