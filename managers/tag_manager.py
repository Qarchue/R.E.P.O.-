import discord
from typing import List, Optional

from database import UserConfiguration, UserRecord, ServerTags

from utility import LOG, config

class TagResolver:
    @staticmethod
    def _get_mod_tag(
        forum: discord.ForumChannel,
        user_record: UserRecord,
        server_tags: ServerTags,
    ) -> Optional[discord.ForumTag]:
        """依據模組碼判斷是否有模組tag"""
        if user_record.mod_code == "0":
            return forum.get_tag(server_tags.no_mods)
        return None

    @staticmethod
    def _get_version_tag(
        forum: discord.ForumChannel,
        user_record: UserRecord,
        server_tags: ServerTags,
    ) -> Optional[discord.ForumTag]:
        """根據遊戲密碼判斷版本tag"""
        if user_record.game_password == "0":
            return forum.get_tag(server_tags.versions['new'])
        else:
            return forum.get_tag(server_tags.versions['beta'])

    @staticmethod
    def _get_custom_tags(
        forum: discord.ForumChannel,
        user_roles: List[discord.Role],
        server_tags: ServerTags,
    ) -> List[discord.ForumTag]:
        """根據自訂標籤判斷tag"""
        tags = []
        for role in user_roles:
            tag_id = server_tags.custom_tags.get(str(role.id))
            if tag_id is not None:
                tag = forum.get_tag(tag_id)
                if tag is not None:
                    tags.append(tag)
        return tags

    @staticmethod
    def get_tags(
        guild: discord.Guild,
        forum: discord.ForumChannel,
        user_roles: List[discord.Role],
        user_record: UserRecord,
        server_tags: ServerTags,
    ) -> List[discord.ForumTag]:
        """
        判斷貼文該用到什麼標籤並回傳
        """
        if guild is None:
            guild = forum.guild
        tag_list = []
        mod_tag = TagResolver._get_mod_tag(forum, user_record, server_tags)
        if mod_tag is not None:
            tag_list.append(mod_tag)

        version_tag = TagResolver._get_version_tag(forum, user_record, server_tags)
        if version_tag is not None:
            tag_list.append(version_tag)

        custom_tags = TagResolver._get_custom_tags(forum, user_roles, server_tags)
        tag_list.extend(custom_tags)

        return tag_list
    
class TagEnsurer:
    @staticmethod
    async def get_or_create_mod_tag(
        forum: discord.ForumChannel,
        tag_id: int | None,
    ) -> int | None:
        # 先檢查 tag_id 是否有效
        tag = forum.get_tag(tag_id) if tag_id is not None else None
        # 再檢查名稱是否已存在
        if tag is None:
            for t in forum.available_tags:
                if t.name == "無模組":
                    return t.id
            tag = await forum.create_tag(name="無模組", emoji="🛠️")
            return tag.id
        return tag.id

    @staticmethod
    async def get_or_create_version_tag(
        forum: discord.ForumChannel,
        versions: dict,
    ) -> dict:
        for version in config.repo_versions:
            tag_id = versions.get(version, 0)
            tag = forum.get_tag(tag_id)
            if tag is None:
                # 先檢查名稱是否已存在
                exist = next((t for t in forum.available_tags if t.name == version), None)
                if exist:
                    versions[version] = exist.id
                else:
                    tag = await forum.create_tag(
                        name=version,
                        emoji="🛠️",
                    )
                    versions[version] = tag.id
        return versions

    @staticmethod
    async def get_or_delete_custom_tags(
        forum: discord.ForumChannel,
        custom_tags: dict,
    ) -> dict:
        returned_tags = {}
        guild = forum.guild
        for role_id, tag_id in custom_tags.items():
            role = guild.get_role(int(role_id))
            tag = forum.get_tag(tag_id)
            if role is None or tag is None:
                continue
            returned_tags[str(role_id)] = tag.id
        return returned_tags

    @staticmethod
    async def get_or_create_tags(
        guild: discord.Guild,
        forum: discord.ForumChannel,
        server_tags: ServerTags,
    ):
        """
        確保標籤存在
        """
        # 確保模組tag存在
        mod_tag = await TagEnsurer.get_or_create_mod_tag(forum, server_tags.no_mods)
        # 確保版本tag存在
        versions = await TagEnsurer.get_or_create_version_tag(forum, server_tags.versions)
        # 確保自訂tag存在
        custom_tags = await TagEnsurer.get_or_delete_custom_tags(forum, server_tags.custom_tags)

        server_tags.no_mods = mod_tag
        server_tags.versions = versions
        server_tags.custom_tags = custom_tags

        return server_tags
class TagManager(TagResolver, TagEnsurer):

    @staticmethod
    async def _set_tags(
        thread: discord.Thread,
        tags: List[discord.ForumTag],
    ):
        # Discord threads最多只能有5個標籤
        if len(tags) > 5:
            tags = tags[:5]
        await thread.edit(applied_tags=tags)

    @staticmethod
    async def set_thread_tag(
        user: discord.Member,
        guild: discord.Guild,
        forum: discord.ForumChannel,
        thread: discord.Thread,
        user_record: UserRecord,
        server_tags: ServerTags,
        unknown_tags: Optional[List[str]] = None,
    ) -> None:
        """
        設定標籤
        """
        user_roles = user.roles
        tags = TagManager.get_tags(
            guild=guild,
            forum=forum,
            user_roles=user_roles,
            user_record=user_record,
            server_tags=server_tags,
        )
        if unknown_tags is not None:
            unknown_tags = TagManager.convert_unknown_tags_to_forum_tags(
                forum=forum,
                unknown_tags=unknown_tags,
            )
            tags.extend(unknown_tags)

            
        await TagManager._set_tags(
            thread=thread,
            tags=tags,
        )

    @staticmethod
    def convert_unknown_tags_to_forum_tags(
        forum: discord.ForumChannel,
        unknown_tags: List[str],
    ) -> List[discord.ForumTag]:
        """
        將 unknown_tags (dict 列表) 轉換成 discord.ForumTag 列表
        """
        tags = []
        for tag_id in unknown_tags:
            tag = forum.get_tag(tag_id)
            if tag is not None:
                tags.append(tag)
        return tags



    def _get_unknown_tags(
        forum: discord.ForumChannel,
        server_tags: ServerTags,
    ) -> List[dict]:
        """取得在 server_tags 裡面沒有的 tag，回傳只包含名稱和ID的字典列表"""
        known_tag_ids = set()
        if server_tags.no_mods:
            known_tag_ids.add(server_tags.no_mods)
        known_tag_ids.update(server_tags.versions.values())
        known_tag_ids.update(server_tags.custom_tags.values())
        return [
            {
                "value": tag.id,
                "label": tag.name,
            }
            for tag in forum.available_tags
            if tag.id not in known_tag_ids
        ]
