import discord
from datetime import datetime
from typing import Optional
from database import UserConfiguration, UserRecord

class create_group_embed:
    @staticmethod
    def create_group(
    ) -> discord.Embed:
        """創建房間的訊息"""
        embed = discord.Embed(
            description=f"## 創建房間中...",
            colour=0x00ff00,
            timestamp=datetime.now()
        )
        return embed
    
    @staticmethod
    def create_group_failed(
    ) -> discord.Embed:
        """創建房間失敗的訊息"""
        embed = discord.Embed(
            description="## 創建房間失敗",
            colour=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="錯誤",
            value="無法創建房間",
            inline=False
        )
        return embed

    @staticmethod
    def create_group_success(
        user_in_voice_channel: bool,
        voice_channel: discord.VoiceChannel,
    ) -> discord.Embed:
        """創建房間成功的訊息"""
        embed = discord.Embed(
            description="## 創建房間成功",
            colour=0x00ff00,
            timestamp=datetime.now()
        )
        if not user_in_voice_channel:
            embed.add_field(
                name="請在一分鐘內加入以創建的語音頻道，否則語音頻道將自動刪除",
                value=f"{voice_channel.mention}",
                inline=False
            )
        return embed

class update_group_embed:
    @staticmethod
    def update_group(
    ) -> discord.Embed:
        """設定房間的訊息"""
        embed = discord.Embed(
            description=f"## 設定中...",
            colour=0x00ff00,
            timestamp=datetime.now()
        )
        return embed
    
    @staticmethod
    def update_group_failed(
    ) -> discord.Embed:
        """設定房間失敗的訊息"""
        embed = discord.Embed(
            description="## 設定房間失敗",
            colour=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(
            name="錯誤",
            value="無法設定房間",
            inline=False
        )
        return embed

    @staticmethod
    def update_group_success(
    ) -> discord.Embed:
        """設定房間成功的訊息"""
        embed = discord.Embed(
            description="## 設定成功",
            colour=0x00ff00,
            timestamp=datetime.now()
        )
        return embed

class join_group_embed:

    @staticmethod
    def join_success(
        limit_mode: Optional[int] = None,
    ) -> None:
        """加入成功的訊息"""
        embed = discord.Embed(
            description=f"## {"密碼正確，" if limit_mode == 3 else ""}正在加入語音頻道...",
            colour=0x00ff00,
            timestamp=datetime.now()
        )
        return embed

    @staticmethod  
    def join_failed(
        user_in_voice_channel: Optional[bool] = None,
        voice_channel_full: Optional[bool] = None,
        limit_mode: Optional[int] = None,
    ) -> discord.Embed:
        """加入失敗的訊息"""
        if user_in_voice_channel is not None:
            description = f"你不在待機語音頻道中"
        if voice_channel_full is not None:
            description = f"語音頻道已滿"
        if limit_mode is not None:
            if limit_mode == 0:
                description = f"錯誤"
            if limit_mode == 1:
                description = f"你不在白名單"
            elif limit_mode == 2:
                description = f"你已被列為黑名單"
            elif limit_mode == 3:
                description = f"密碼錯誤"

        embed = discord.Embed(
            description="## 無法加入語音頻道",
            colour=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(
            name=description,
            value="",
            inline=False
        )
        return embed


class EmbedManager(create_group_embed, update_group_embed, join_group_embed):

    





    @staticmethod
    def description(
        user_record: UserRecord,
        user_config: UserConfiguration,
        voice_channel: discord.VoiceChannel,
    ) -> discord.Message:
        server = voice_channel.guild

        embed=discord.Embed(description=f"# **{user_record.group_name}**", colour=0x4100ff)
        embed.add_field(name=f"{user_record.group_description}", value="", inline=False)

        if user_record.mod_code != "0":
            embed.add_field(name="📝模組碼:",
                            value=f" - {user_record.mod_code}",
                            inline=False)
        if user_record.game_password != "0":
            embed.add_field(name="🔐房間密碼:",
                            value=f" - {user_record.game_password}",
                            inline=False)
        if user_config.steam_friend_code is not None:
            embed.add_field(name="房主好友碼:",
                            value=f" - {user_config.steam_friend_code}",
                            inline=False)
        embed.add_field(
            name="語音頻道",
            value=f" - {voice_channel.mention}",
            inline=False
        )
        embed.set_footer(
            text="揪團", 
            icon_url=server.icon.url if server.icon else None
        )
        return embed