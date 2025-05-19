import sqlalchemy
import discord
import re

from discord.ext import commands

from discord import app_commands
from typing import Optional

from database import Database, WhiteList, BlackList, ServerConfiguration, Server, UserConfiguration, User

from utility import SlashCommandLogger, LOG, config, steam_API


class UserCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @app_commands.command(name="好友碼", description="設定自己的steam好友碼")
    @app_commands.rename(friend_code="參數")
    @SlashCommandLogger
    async def set_steam_friend_code(
        self, interaction: discord.Interaction, friend_code: int,
    ):
        server_config = await Database.select_one(ServerConfiguration, ServerConfiguration.server_id.is_(interaction.guild.id))
        if server_config.steamAPI_key == None:
            await interaction.response.send_message("❌ 錯誤: 伺服器尚未設定 Steam API Key **請聯絡管理員**", ephemeral=True, )
            return
        try:
            await steam_API.is_valid_steam_friend_code(friend_code, server_config.steamAPI_key)
        except steam_API.InvalidAPIKeyError:
            await interaction.response.send_message("❌ 錯誤: Steam API Key 錯誤", ephemeral=True, )
            return
        except steam_API.UserNotFoundError:
            await interaction.response.send_message("❌ 錯誤: 找不到該使用者", ephemeral=True, )
            return
        except steam_API.SteamAPIError:
            await interaction.response.send_message("❌ 錯誤: Steam API 錯誤", ephemeral=True, )
            return
        except steam_API.SteamNetworkError:
            await interaction.response.send_message("❌ 錯誤: Steam 網路錯誤", ephemeral=True, )
            return
        except Exception as e:
            LOG.System(f"錯誤: {e}")
            await interaction.response.send_message("❌ 錯誤: 無法驗證該使用者", ephemeral=True, )
            return

        else:
            """如果找到使用者，則將好友碼存入資料庫"""
            user_config = await Database.select_one(UserConfiguration, UserConfiguration.discord_id.is_(interaction.user.id))
            user_config.steam_friend_code = friend_code
            await Database.insert_or_replace(user_config)
            await interaction.response.send_message(f"✅ 已將好友碼設為: `{friend_code}`", ephemeral=True, )






async def setup(client: commands.Bot):
    await client.add_cog(UserCommandsCog(client))
