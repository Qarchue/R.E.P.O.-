import sqlalchemy
import discord

from discord.ext import commands

from discord import app_commands

from database import Database, WhiteList, BlackList, ServerConfiguration, Server, UserConfiguration, User, ServerTags

from utility import SlashCommandLogger, LOG, config, steam_API




class AdminCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot



    @commands.has_permissions(administrator=True)
    @app_commands.command(name="set_api_key", description="設定steamAPI key")
    @app_commands.rename(API_key="api_key")
    @SlashCommandLogger
    async def set_steamAPI_key(
        self, interaction: discord.Interaction, API_key: str,
    ):
        try:
            await steam_API.verify_steam_api_key(API_key)
        except steam_API.InvalidAPIKeyError:
            await interaction.response.send_message("❌ 錯誤: Steam API Key 錯誤", ephemeral=True, )
        except steam_API.SteamAPIError:
            await interaction.response.send_message("❌ 錯誤: Steam API 錯誤", ephemeral=True, )
        except steam_API.SteamNetworkError:
            await interaction.response.send_message("❌ 錯誤: Steam 網路錯誤", ephemeral=True, )
        else:
            server_config = await Database.select_one(ServerConfiguration, ServerConfiguration.server_id.is_(interaction.guild.id))
            server_config.steamAPI_key = API_key
            await Database.insert_or_replace(server_config)
            await interaction.response.send_message(f"✅ 已成功設定API key `{API_key}`", ephemeral=True, )

    @commands.has_permissions(administrator=True)
    @app_commands.command(name="自訂標籤綁定", description="自訂標籤綁定/查詢/刪除")
    @app_commands.rename(role="身份組", tag_id="標籤")
    @SlashCommandLogger
    async def set_custom_tags(
        self, interaction: discord.Interaction, role: discord.Role = None, tag_id: str = None
    ):
        guild = interaction.guild
        await interaction.response.defer(ephemeral=True)
        server_config = await Database.select_one(ServerConfiguration, ServerConfiguration.server_id.is_(guild.id))
        server_tags = await Database.select_one(ServerTags, ServerTags.server_id.is_(guild.id))

        if server_tags is None:
            await interaction.followup.send(
                content="伺服器尚未設定揪團頻道，請先設定揪團頻道",
                ephemeral=True,
            )
            return

        # 顯示清單
        if role is None or tag_id is None:
            if not server_tags.custom_tags:
                await interaction.followup.send(
                    content="目前沒有任何標籤綁定。",
                    ephemeral=True,
                )
                return
            lines = []
            forum = guild.get_channel(server_config.looking_for_group_channel)
            for role_id, tag_id in server_tags.custom_tags.items():
                role_obj = guild.get_role(int(role_id))
                tag_obj = forum.get_tag(int(tag_id)) if forum else None
                role_name = role_obj.name if role_obj else f"未知身份組({role_id})"
                tag_name = tag_obj.name if tag_obj else f"未知標籤({tag_id})"
                lines.append(f"{role_name} ➔ {tag_name}")
            await interaction.followup.send(
                content="目前標籤綁定清單：\n" + "\n".join(lines),
                ephemeral=True,
            )
            return

        # 檢查 forum
        forum = guild.get_channel(server_config.looking_for_group_channel)
        if forum is None:
            await interaction.followup.send(
                content="伺服器尚未設定揪團頻道，請先設定揪團頻道",
                ephemeral=True,
            )
            return

        try:
            tag_id_int = int(tag_id)
        except ValueError:
            await interaction.followup.send(
                content="標籤ID格式錯誤，請輸入正確的標籤ID。",
                ephemeral=True,
            )
            return

        tag = forum.get_tag(tag_id_int)
        if tag is None:
            await interaction.followup.send(
                content="標籤不存在，請確認標籤ID是否正確",
                ephemeral=True,
            )
            return

        # 若已存在且一樣，則刪除
        if str(role.id) in server_tags.custom_tags and server_tags.custom_tags[str(role.id)] == tag.id:
            del server_tags.custom_tags[str(role.id)]
            await Database.insert_or_replace(server_tags)
            await interaction.followup.send(
                content=f"已移除身份組 `{role.name}` 與標籤 `{tag.name}` 的綁定。",
                ephemeral=True,
            )
            return

        # 新增或更新綁定
        server_tags.custom_tags[str(role.id)] = tag.id
        await Database.insert_or_replace(server_tags)
        await interaction.followup.send(
            content=f"已成功將標籤 `{tag.name}` 綁定至身份組 `{role.name}`",
            ephemeral=True,
        )


    @commands.has_permissions(administrator=True)
    @app_commands.command(name="設定提及身份組", description="設定或移除伺服器 提及身份組")
    @app_commands.rename(role="身份組")
    @SlashCommandLogger
    async def set_mention_role(
        self, interaction: discord.Interaction, role: discord.Role = None
    ):
        guild = interaction.guild
        await interaction.response.defer(ephemeral=True)
        server_config = await Database.select_one(ServerConfiguration, ServerConfiguration.server_id.is_(guild.id))

        if role is None:
            if server_config.mention_role is None:
                await interaction.followup.send(
                    content="目前尚未設定 mention_role。",
                    ephemeral=True,
                )
            else:
                role_obj = guild.get_role(server_config.mention_role)
                role_name = role_obj.name if role_obj else f"未知身份組({server_config.mention_role})"
                await interaction.followup.send(
                    content=f"目前 mention_role 為 `{role_name}`。",
                    ephemeral=True,
                )
            return

        # 若已存在且一樣，則刪除
        if server_config.mention_role == role.id:
            server_config.mention_role = None
            await Database.insert_or_replace(server_config)
            await interaction.followup.send(
                content=f"已移除 mention_role `{role.name}`。",
                ephemeral=True,
            )
            return

        # 新增或更新 mention_role
        server_config.mention_role = role.id
        await Database.insert_or_replace(server_config)
        await interaction.followup.send(
            content=f"已成功設定 mention_role 為 `{role.name}`。",
            ephemeral=True,
        )

async def setup(client: commands.Bot):
    await client.add_cog(AdminCommandsCog(client))
