import sqlalchemy
import discord
import re

from discord.ext import commands
from discord import app_commands
from typing import Optional, List

from database import Database, WhiteList, BlackList
from utility import SlashCommandLogger
from .ui import page_list

from managers import GroupManager

class mentions_converter(app_commands.Transformer):
    @staticmethod
    async def transform(interaction: discord.Interaction, value: str) -> List[discord.Member]:
        user_ids = re.findall(r"<@!?(\d+)>", value)
        members = [interaction.guild.get_member(int(uid)) for uid in user_ids]
        members = [m for m in members if m is not None]
        return list(set(members)) if members else None


class ListManagerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_color_and_model(self, list_type: str):
        if list_type == "whitelist":
            return (
                WhiteList,
                discord.Color.from_rgb(190, 255, 190),
                discord.Color.from_rgb(190, 190, 190),
                discord.Color.from_rgb(255, 255, 255)
            )
        else:
            return (
                BlackList,
                discord.Color.from_rgb(0, 65, 0),
                discord.Color.from_rgb(65, 65, 65),
                discord.Color.from_rgb(0, 0, 0)
            )

    async def _process_list_command(
            self, 
            interaction: discord.Interaction, 
            model: WhiteList|BlackList, 
            member_metions: Optional[str], 
            add_color: discord.Color, 
            remove_color: discord.Color, 
            view_color: discord.Color, 
            list_type: str,
    ):
        """
        處理白名單或黑名單的指令

        """
        user = interaction.user

        if member_metions:
            members = await mentions_converter.transform(interaction, member_metions)
            if not members:
                await interaction.followup.send("❌ 錯誤: 找不到使用者", ephemeral=True)
                return

            _add_list = page_list.member_list(name="增加", color=add_color)
            _remove_list = page_list.member_list(name="移除", color=remove_color)

            for member in members:
                entry = await Database.select_one(
                    model, 
                    sqlalchemy.and_(model.discord_id == member.id, model.user_id == user.id)
                )
                
                if entry is None:
                    await Database.insert_or_replace(model(discord_id=member.id, user_id=user.id))
                    _add_list.add_member(member)
                else:
                    await Database.delete_instance(entry)
                    _remove_list.add_member(member)
            await page_list.send_form_pages(interaction, f"{list_type}操作", [_add_list, _remove_list])
        else:
            entries = await Database.select_all(model, model.user_id == user.id)
            _view_list = page_list.member_list(name="檢視", color=view_color, show_when_empty=True)
            for entry in entries:
                member = interaction.guild.get_member(entry.discord_id)
                if member:
                    _view_list.add_member(member)

            await page_list.send_form_pages(interaction, list_type, [_view_list])




    @app_commands.command(name="白名單", description="白名單操作")
    @app_commands.rename(member_metions="使用者")
    @SlashCommandLogger
    async def set_whitelist(self, interaction: discord.Interaction, member_metions: Optional[str] = None):
        model, add_color, remove_color, view_color = self.get_color_and_model("whitelist")
        await interaction.response.defer(ephemeral=True)
        await self._process_list_command(interaction, model, member_metions, add_color, remove_color, view_color, "白名單")
        await GroupManager.change_limit(
            interaction=interaction,
            limit_mode=1,
        )

    @app_commands.command(name="黑名單", description="黑名單操作")
    @app_commands.rename(member_metions="使用者")
    @SlashCommandLogger
    async def set_blacklist(self, interaction: discord.Interaction, member_metions: Optional[str] = None):
        model, add_color, remove_color, view_color = self.get_color_and_model("blacklist")
        await interaction.response.defer(ephemeral=True)
        await self._process_list_command(interaction, model, member_metions, add_color, remove_color, view_color, "黑名單")
        await GroupManager.change_limit(
            interaction=interaction,
            limit_mode=2,
        )

async def setup(client: commands.Bot):
    await client.add_cog(ListManagerCog(client))
