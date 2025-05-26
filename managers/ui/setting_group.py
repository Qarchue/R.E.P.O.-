from typing import List, Optional

import discord
import sqlalchemy
from utility import LOG, EmbedTemplate
from database import Database, UserConfiguration, UserRecord, Group


class SettingGroupModal(discord.ui.Modal, title="設定揪團"):

    group_name: discord.ui.TextInput = discord.ui.TextInput(
        label="房間名稱",
        placeholder="房間名稱",  
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=20,
    )
    group_description: discord.ui.TextInput = discord.ui.TextInput(
        label="備註",
        placeholder="備註",  
        style=discord.TextStyle.long,
        required=True,
        min_length=1,
        max_length=200,
    )
    voice_name: discord.ui.TextInput = discord.ui.TextInput(
        label="語音名稱",
        placeholder="語音名稱",  
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=20,
    )
    mod_code: discord.ui.TextInput = discord.ui.TextInput(
        label="模組碼",
        placeholder="模組碼",  
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=50,
    )
    game_password: discord.ui.TextInput = discord.ui.TextInput(
        label="遊戲密碼",
        placeholder="遊戲密碼",  
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=20,
    )

    """創建房間表單"""
    def __init__(
        self, 
        user_record: UserRecord, 
        user_config: UserConfiguration, 
        callback: Optional[callable],
    ):
        self.callback = callback
        self.user_record = user_record
        self.user_config = user_config

        self.group_name.placeholder = f"請輸入房間名稱(初次使用必填)" if (user_record.group_name is None) else f"請輸入房間名稱(不輸入則使用上次的名稱: {user_record.group_name})"
        self.group_name.required = (user_record.group_name is None)
        self.group_description.placeholder = f"請輸入房間備註(初次使用必填)" if (user_record.group_description is None) else f"請輸入房間備註(不輸入則使用上次的備註: {user_record.group_description})"
        self.group_description.required = (user_record.group_description is None)
        self.voice_name.placeholder = f"請輸入語音名稱(初次使用必填)" if (user_record.voice_name is None) else f"請輸入語音名稱(不輸入則使用上次的名稱: {user_record.voice_name})"
        self.voice_name.required = (user_record.voice_name is None)
        self.mod_code.placeholder = f"請貼上模組碼(不使用則輸入0)" if (user_record.mod_code is None) else f"請貼上模組碼(不輸入則使用上次的: {user_record.mod_code})"
        self.mod_code.required = (user_record.mod_code is None)
        self.game_password.placeholder = f"請輸入遊戲密碼(不使用則輸入0)" if (user_record.game_password is None) else f"請輸入遊戲密碼(不輸入則使用上次的: {user_record.game_password})"
        self.game_password.required = (user_record.game_password is None)
        # 呼叫父類別初始化
        super().__init__()

    async def on_submit(self, interaction: discord.Interaction):
        # 處理表單資料提交
        user = interaction.user
        guild = interaction.guild
        user_record = self.user_record
        user_config = self.user_config
        if self.group_name.value.strip() != "":
            user_record.group_name = self.group_name.value
        if self.group_description.value.strip() != "":
            user_record.group_description = self.group_description.value
        if self.voice_name.value.strip() != "":
            user_record.voice_name = self.voice_name.value
        if self.mod_code.value.strip() != "":
            user_record.mod_code = self.mod_code.value
        if self.game_password.value.strip() != "":
            user_record.game_password = self.game_password.value
        # 儲存資料
        await Database.insert_or_replace(user_record)

        try:
            await self.callback(
                interaction=interaction,
                user_record=user_record,
                user_config=user_config,
            )
        except Exception as e:
            LOG.Error(f"創建房間失敗: {e}")
