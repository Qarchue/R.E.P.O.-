import asyncio
from typing import List, Optional

import discord
import sqlalchemy
from discord.ext import commands

from database import (
    Database, 
    Group, 
    UserRecord,
    ServerTags,
    UserConfiguration, 
    ServerConfiguration,
)

from .ui.thread_menu import ThreadMenuNav
from .ui.join_button import JoinButtonView
from .ui.create_button import CreateButtonView
from .ui.setting_group import SettingGroupModal
from .ui.enter_password import EnterPasswordModal

from managers.tag_manager import TagManager
from managers.view_manager import ViewManager
from managers.embed_manager import EmbedManager
from managers.forum_manager import ForumManager
from managers.thread_manager import ThreadManager
from managers.member_manager import MemberManager
from managers.database_manager import DatabaseManager
from managers.permission_manager import PermissionManager
from managers.voice_channel_manager import VoiceChannelManager

from utility import LOG, TimeoutOperation


class GroupManager:
    enter_password = EnterPasswordModal
    tag_manager = TagManager

    async def create(
        interaction: discord.Interaction,
        user_record: Optional[UserRecord] = None,
        user_config: Optional[UserConfiguration] = None,
        server_config: Optional[ServerConfiguration] = None,
    ) -> None:
        guild = interaction.guild
        """伺服器"""
        user = interaction.user
        """創建者"""
        await interaction.response.send_message(
            embed=EmbedManager.create_group(
            ),
            ephemeral=True,
        )
        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=user.id,
            user_record=user_record,
            user_config=user_config,
            server_config=server_config,
            server_tags=None,
        )
        """填充缺失的資料"""
        user_record = filled_data.user_record
        user_config = filled_data.user_config
        server_config = filled_data.server_config
        server_tags = filled_data.server_tags

        waiting_channel = guild.get_channel(server_config.waiting_room_channel)
        forum = guild.get_channel(server_config.looking_for_group_channel)
        voice_category = waiting_channel.category

        """待機語音頻道的類別"""
        voice_channel = await VoiceChannelManager.create_voice_channel(
            guild=guild,
            category=voice_category,
            user_limit=user_config.user_limit,
            channel_name=user_record.voice_name,
        )
        await GroupManager.change_limit(
            interaction=interaction,
            limit_mode=user_config.limit_mode,
            voice_channel=voice_channel,
        )
        thread = await ThreadManager.create(
            user=user,
            name=user_record.group_name,
            content=user_record.group_description,
            forum=forum,
        )
        await TagManager.set_thread_tag(
            user=user,
            guild=guild,
            forum=forum,
            thread=thread,
            user_record=user_record,
            server_tags=server_tags,
        )
        
        view = ThreadMenuNav(
            guild=guild,
            user_config=user_config,
            user_record=user_record,
            group_manager=GroupManager,
            allowed_user=user,
        )
        await thread.send(view=view)
        embed = EmbedManager.description(
            user_record=user_record,
            user_config=user_config,
            voice_channel=voice_channel,
        )


        # 嘗試取得伺服器設定中的 mention_role_id
        mention_role_id = getattr(server_config, "mention_role", None)
        mention_role = None
        if mention_role_id:
            mention_role = guild.get_role(mention_role_id)
        # 如果有 mention_role，則在 content 中提及，否則 content 為空字串
        content = mention_role.mention if mention_role else ""


        description_message = await thread.send(
            content=content,
            embed=embed,
            view=JoinButtonView(
            owner=user,
            voice_channel=voice_channel,
            group_manager=GroupManager,
            )
        )
        group = Group(
            owner_id=user.id,
            server_id=guild.id,
            voice_channel_id=voice_channel.id,
            thread_id=thread.id,
            description_message_id=description_message.id,
        )  
        await DatabaseManager.save_data(group=group) 


        await GroupManager.auto_delete_voice_channel(
            guild=guild,
            voice_channel=voice_channel,
        )

        if await MemberManager.check_user_in_voice_channel(
            user=user,
            voice_channel=waiting_channel,
        ):
            await interaction.edit_original_response(
                embed=EmbedManager.create_group_success(
                    user_in_voice_channel=True,
                    voice_channel=voice_channel,
                ),
            )
            await MemberManager.move_user_to_channel(
                user=user,
                voice_channel=voice_channel,
            )

        else:
            await interaction.edit_original_response(
                embed=EmbedManager.create_group_success(
                    user_in_voice_channel=False,
                    voice_channel=voice_channel,
                )
            )
        LOG.System(f"使用者{LOG.User(user.id)}創建房間")

    async def delete(
        guild: discord.Guild,
        user_id: int,
        group: Optional[Group] = None,
        user_record: Optional[UserRecord] = None,
        user_config: Optional[UserConfiguration] = None,
        server_config: Optional[ServerConfiguration] = None,
        voice_channel: Optional[discord.VoiceChannel] = None,
        thread: Optional[discord.Thread] = None,
    ) -> None:

        LOG.System(f"使用者{LOG.User(user_id)}刪除房間")        
        
        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=user_id,
            group=group,
            user_record=user_record,
            user_config=user_config,
            server_config=server_config,
        )
        user_record = filled_data.user_record
        user_config = filled_data.user_config

        group: Group = filled_data.group

        if voice_channel is None:
            voice_channel = guild.get_channel(group.voice_channel_id)
        if thread is None:
            thread = guild.get_thread(group.thread_id)

        if voice_channel is not None:
            user_record.voice_name = voice_channel.name
            user_config.user_limit = voice_channel.user_limit

        await VoiceChannelManager.delete_voice_channel(
            voice_channel=voice_channel,
        )
                
        await ThreadManager.delete(
            thread=thread,
        )
        

        await DatabaseManager.save_data(
            user_record=user_record,
            user_config=user_config,
        )

        await DatabaseManager.delete_data(group=group)

        LOG.System(f"使用者{LOG.User(user_id)}刪除房間成功")

    async def update(
        interaction: discord.Interaction,
        unknown_tags: Optional[List[dict]] = None,
        user_record: Optional[UserRecord] = None,
        user_config: Optional[UserConfiguration] = None,
        server_config: Optional[ServerConfiguration] = None,
        server_tags: Optional[List[ServerConfiguration]] = None,
    ):
        guild = interaction.guild
        user = interaction.user
        await interaction.response.send_message(
            embed=EmbedManager.update_group(),ephemeral=True,)
        group = await Database.select_one(
            Group,
            sqlalchemy.and_(
                Group.server_id == guild.id,
                Group.owner_id == user.id
            )
        )
        if group is None:
            return

        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=user.id,
            group=None,
            user_record=user_record,
            user_config=user_config,
            server_config=server_config,
            server_tags=server_tags,
        )
        user_record: UserRecord = filled_data.user_record
        user_config: UserConfiguration = filled_data.user_config
        server_config: ServerConfiguration = filled_data.server_config
        server_tags: ServerTags = filled_data.server_tags


        forum = guild.get_channel(server_config.looking_for_group_channel)
        thread = guild.get_thread(group.thread_id)
        await ThreadManager.update_thread(
            thread=thread,
            name=user_record.group_name,
            content=user_record.group_description,
        )
        await TagManager.set_thread_tag(
            user=user,
            guild=guild,
            forum=forum,
            thread=thread,
            user_record=user_record,
            server_tags=server_tags,
            unknown_tags=unknown_tags,
        )
        voice_channel = guild.get_channel(group.voice_channel_id)
        await VoiceChannelManager.update_voice_channel(
            voice_channel=voice_channel,
            channel_name=user_record.voice_name
        )
        try:
            description_message = await thread.fetch_message(group.description_message_id)
        except discord.NotFound:
            description_message = await thread.send(
                content="",
                view=JoinButtonView(
                    owner=user,
                    voice_channel=voice_channel,
                    group_manager=GroupManager,
                )
            )
            group.description_message_id = description_message.id
            await DatabaseManager.save_data(
                group=group,
            )
        await description_message.edit(
            embed=EmbedManager.description(
                user_record=user_record,
                user_config=user_config,
                voice_channel=voice_channel,
            )
        )


        await interaction.edit_original_response(embed=EmbedManager.update_group_success())

        LOG.System(f"使用者{LOG.User(user.id)}更新房間")

    @staticmethod
    async def get_unknown_tags(
        interaction: discord.Interaction,
    ) -> List[dict]:
        guild = interaction.guild
        user = interaction.user
        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=user.id,
            server_config=None,
            server_tags=None,
        )
        server_config: ServerConfiguration = filled_data.server_config
        server_tags: ServerTags = filled_data.server_tags
        forum = guild.get_channel(server_config.looking_for_group_channel)
        tags = TagManager._get_unknown_tags(
            forum=forum,
            server_tags=server_tags,
        )
        return tags



    @staticmethod
    async def change_limit(
        interaction: discord.Interaction,
        limit_mode: int,
        voice_channel: Optional[discord.VoiceChannel] = None,
    ) -> None:
        try:
            guild = interaction.guild
            user = interaction.user
            white_list = []
            black_list = []

            if limit_mode == 1:
                # 白名單模式
                white_list = None
            elif limit_mode == 2:
                # 黑名單模式
                black_list = None

            filled_data = await DatabaseManager.fill_missing_data(
                guild_id=guild.id,
                user_id=user.id,
                user_config=None,
                white_list=white_list,
                black_list=black_list,
            )
            
            user_config: UserConfiguration = filled_data.user_config

            if voice_channel is None:
                group_data = await DatabaseManager.fill_missing_data(
                    guild_id=guild.id,
                    user_id=user.id,
                    group=None,
                )
                group: Group = group_data.group
                voice_channel = guild.get_channel(group.voice_channel_id)


            await PermissionManager.change_limit(
                guild=guild,
                user=user,
                voice_channel=voice_channel,
                white_list=filled_data.white_list,
                black_list=filled_data.black_list,
                limit_mode=limit_mode,
            )
            await VoiceChannelManager.change_limit(
                guild=guild,
                user=user,
                voice_channel=voice_channel,
                white_list=filled_data.white_list,
                black_list=filled_data.black_list,
                limit_mode=limit_mode,
            )
            user_config.limit_mode = limit_mode
            await DatabaseManager.save_data(user_config=user_config)

        except Exception as e:
            LOG.Error(f"更改權限失敗: {e}")


    @staticmethod
    async def change_list(
        interaction: discord.Interaction,
        limit_mode: int,
    ) -> None:

        guild = interaction.guild
        user = interaction.user

        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=user.id,
            user_config=None,
        )
        user_config: UserConfiguration = filled_data.user_config
        if limit_mode == user_config.limit_mode:
            await GroupManager.change_limit(
                interaction=interaction,
                limit_mode=limit_mode,
            )


    @staticmethod
    async def handle_join(
        interaction: discord.Interaction,
        voice_channel: discord.VoiceChannel,
        owner: discord.Member,
    ) -> bool:
        
        guild = interaction.guild
        user = interaction.user

        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=owner.id,
            server_config=None,
            user_config=None,
            white_list=None,
            black_list=None,
        )
        
        user_config: UserConfiguration = filled_data.user_config
        server_config: ServerConfiguration = filled_data.server_config
        
        waiting_voice = guild.get_channel(server_config.waiting_room_channel)

        user_in_voice = await MemberManager.check_user_in_voice_channel(user=user, voice_channel=waiting_voice)
        if not user_in_voice:
            await interaction.response.send_message(
                embed=EmbedManager.join_failed(
                    user_in_voice_channel=True,
                ), ephemeral=True
            )
            LOG.Debug(f"使用者{LOG.User(user.id)}不在待機頻道")
            return
        
        try:
            voice_full = VoiceChannelManager.user_limit_check(
                voice_channel=voice_channel,
            )
            

            if voice_full:
                await interaction.response.send_message(
                    embed=EmbedManager.join_failed(
                        voice_channel_full=True,
                    ), ephemeral=True
                )
                LOG.Debug(f"使用者{LOG.User(user.id)}頻道已滿")
                return
            
        except Exception as e:
            LOG.Error(f"使用者{LOG.User(user.id)}加入頻道失敗: {e}")

        
        try:        
            await PermissionManager.check_join_permission(
                interaction=interaction,
                limit_mode=user_config.limit_mode,
                voice_channel=voice_channel,
                parent=GroupManager,
                white_list=filled_data.white_list,
                black_list=filled_data.black_list,
                password=user_config.group_password,
            )
            LOG.Debug(f"1")
        except Exception as e:
            LOG.Error(f"pcjp: {e}")


    @staticmethod
    async def _handle_permission_check(
        interaction: discord.Interaction,
        user: discord.Member,
        voice_channel: discord.VoiceChannel,
        limit_mode: int,
        move: bool,
    ) -> None:
        if move:
            await MemberManager.move_user_to_channel(
                user=user,
                voice_channel=voice_channel,
            )
            await interaction.response.send_message(
                embed=EmbedManager.join_success(
                    limit_mode=limit_mode,
                ), ephemeral=True
            )
            LOG.Debug(f"使用者{LOG.User(user.id)}已移動到頻道{voice_channel.name}")
        else:
            await interaction.response.send_message(
                embed=EmbedManager.join_failed(
                    limit_mode=limit_mode,
                ), ephemeral=True
            )
            LOG.Debug(f"使用者{LOG.User(user.id)}不在白名單或黑名單中")
            pass


    @staticmethod
    async def ensure_channels(
        guild: discord.Guild,
        user: discord.Member,
        category: discord.CategoryChannel,
        thread_name: str,
        thread_content: str,
        button_content: str,

    ) -> None:
        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=user.id,
            server_config=None,
            server_tags=None,
        )
        server_config: ServerConfiguration = filled_data.server_config
        server_tags: ServerTags = filled_data.server_tags

        forum = await ForumManager.ensure_forum(
            guild=guild,
            channel_id=server_config.looking_for_group_channel,
            category=category,
        )
        thread = await ThreadManager.ensure_thread(
            forum=forum,
            thread_id=server_config.thread_id,
            name=thread_name,
            content=thread_content,
        )
        tags = await TagManager.get_or_create_tags(
            guild=guild,
            forum=forum,
            server_tags=server_tags,
        )
        voice_channel = await VoiceChannelManager.ensure_voice_channel(
            guild=guild,
            channel_id=server_config.waiting_room_channel,
            category=category,
            user_limit=0,
        )

        button_message = await ViewManager.ensure_create_button(
            thread=thread,
            button_message_id=server_config.create_group_button,
            button_content=button_content,
            view=CreateButtonView,
            group_manager=GroupManager,
            setting_group_modal=SettingGroupModal,
        )

        server_config.looking_for_group_channel = forum.id
        server_config.thread_id = thread.id
        server_config.waiting_room_channel = voice_channel.id
        server_config.create_group_button = button_message.id


        await DatabaseManager.save_data(
            server_config=server_config,
            server_tags=tags,
        )


    @staticmethod
    async def add_views(
        bot: commands.Bot,
        guild: discord.Guild,
        user: discord.Member,
        user_record: Optional[UserRecord] = None,
        user_config: Optional[UserConfiguration] = None,
        voice_channel: Optional[discord.VoiceChannel] = None,
    ) -> None:
        filled_data = await DatabaseManager.fill_missing_data(
            guild_id=guild.id,
            user_id=user.id,
            user_record=user_record,
            user_config=user_config,
            group=None,
        )
        user_record: UserRecord = filled_data.user_record
        user_config: UserConfiguration = filled_data.user_config
        group: Group = filled_data.group
        if voice_channel is None:
            voice_channel = guild.get_channel(group.voice_channel_id)


        await ViewManager.add_join_button_view(
            bot=bot,
            join_button_view=JoinButtonView,
            owner=user,
            voice_channel=voice_channel,
            group_manager=GroupManager,
        )
        await ViewManager.add_thread_menu_view(
            bot=bot,
            thread_menu_view=ThreadMenuNav,
            guild=guild,
            user_config=user_config,
            user_record=user_record,
            group_manager=GroupManager,
            allowed_user=user,
        )


    @staticmethod
    async def auto_delete_voice_channel(
        guild: discord.Guild,
        voice_channel: discord.VoiceChannel,
    ) -> None:
        """
        自動刪除語音頻道的邏輯。
        如果語音頻道沒人，啟動計時器；如果有人，取消計時器。

        :param guild: Discord 伺服器
        :param voice_channel: Discord 語音頻道
        """
        group = await Database.select_one(
            Group,
            sqlalchemy.and_(
                Group.server_id.is_(guild.id),
                Group.voice_channel_id.is_(voice_channel.id)
            )
        )
        if group is None:
            return

        if len(voice_channel.members) == 0:
            # 如果頻道沒人，啟動計時器
            await TimeoutOperation.start_timer(
                channel=voice_channel,
                timeout=60,  # 設定計時器為 60 秒
                on_timeout=lambda: asyncio.create_task(
                    GroupManager.delete(
                        guild=guild,
                        user_id=group.owner_id,
                        group=group,
                    )
                )
            )
        else:
            # 如果頻道有人，取消計時器
            await TimeoutOperation.cancel_timer(channel_id=voice_channel.id)