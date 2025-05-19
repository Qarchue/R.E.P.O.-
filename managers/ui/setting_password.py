from typing import List, Optional

import discord


from utility import LOG, EmbedTemplate

from database import Database, WhiteList, BlackList, ServerConfiguration, Server, UserConfiguration, User, UserRecord, Group



class SettingPasswordModal(discord.ui.Modal, title="設定密碼"):

    group_password: discord.ui.TextInput = discord.ui.TextInput(
        label="房間密碼",
        placeholder="房間密碼",  
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=30,
    )
    """設定密碼表單"""
    def __init__(self, user_config: UserConfiguration, callback: Optional[callable] = None):
        self.user_config = user_config
        self.callback = callback
        self.group_password.placeholder = f"請輸入房間密碼(初次使用必填)" if (user_config.group_password is None) else f"請輸入房間密碼(不輸入則使用上次的密碼: {user_config.group_password})"
        self.group_password.required = (user_config.group_password is None)

        # 呼叫父類別初始化
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.user_config.group_password = self.group_password.value
            await Database.insert_or_replace(self.user_config)

            if self.callback is None:
                await interaction.response.send_message(
                    embed=EmbedTemplate.normal(f"房間密碼已設為: {self.group_password.value}"),
                    ephemeral=True,
                )
            
            else:
                await self.callback(interaction, 3)
                await interaction.followup.send(
                    embed=EmbedTemplate.normal(f"房間密碼已設為: {self.group_password.value}"),
                    ephemeral=True,
                )

        except Exception as e:
            LOG.Error(f"密碼設定失敗: {e}")
