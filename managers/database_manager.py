from typing import Optional, Any, List
import discord
from database import Database, UserRecord, UserConfiguration, ServerConfiguration, ServerTags, WhiteList, BlackList, Group
import sqlalchemy
from utility import LOG

_UNSET = object()  # 特殊標記用於檢測未傳入參數

class FilledData:
    __slots__ = ('user_id', 'guild_id', 'group', 'user_record', 'user_config', 'server_config', 'server_tags', 'black_list', 'white_list')
    
    def __init__(self, user_id: int, guild_id: int, **resolved_values):
        self.user_id = user_id
        self.guild_id = guild_id
        for key, value in resolved_values.items():
            setattr(self, key, value)

    def __repr__(self):
        attrs = [f'{k}={getattr(self, k)!r}' for k in self.__slots__ if hasattr(self, k)]
        return f'FilledData({", ".join(attrs)})'

class DatabaseManager:
    @classmethod
    async def _resolve_value(
        cls,
        user_id: int,
        guild_id: int,
        value: Any,
        field_name: str
    ) -> Any:
        """核心解析邏輯"""
        if value is not None:  # 非 None 直接返回
            return value
            
        # 根據字段名稱執行不同解析邏輯
        resolver = {
            'group': cls._fetch_group,
            'user_record': cls._fetch_user_record,
            'user_config': cls._fetch_user_config,
            'server_config': cls._fetch_server_config,
            'server_tags': cls._fetch_server_tags,
            'black_list': cls._fetch_black_list,
            'white_list': cls._fetch_white_list
        }.get(field_name)
        
        return await resolver(user_id, guild_id) if resolver else None

    @staticmethod
    async def _fetch_group(user_id: int, guild_id: int) -> Group:
        """獲取用戶的群組"""
        return await Database.select_one(Group, Group.owner_id.is_(user_id))

    @staticmethod
    async def _fetch_user_record(user_id: int, guild_id: int) -> UserRecord:
        """獲取用戶記錄"""
        return await Database.select_one(UserRecord, UserRecord.discord_id.is_(user_id))
    @staticmethod
    async def _fetch_user_config(user_id: int, guild_id: int) -> UserConfiguration:
        """獲取用戶配置"""
        return await Database.select_one(UserConfiguration, UserConfiguration.discord_id.is_(user_id))

    @staticmethod
    async def _fetch_server_config(user_id: int, guild_id: int) -> ServerConfiguration:
        """獲取伺服器配置"""
        return await Database.select_one(ServerConfiguration, ServerConfiguration.server_id.is_(guild_id))

    @staticmethod
    async def _fetch_black_list(user_id: int, guild_id: int) -> list[BlackList]:
        """獲取黑名單"""
        return await Database.select_all(BlackList,  BlackList.user_id.is_(user_id))
    @staticmethod
    async def _fetch_white_list(user_id: int, guild_id: int) -> list[WhiteList]:
        """獲取白名單"""
        return await Database.select_all(WhiteList, WhiteList.user_id.is_(user_id))
    @staticmethod
    async def _fetch_server_tags(user_id: int, guild_id: int) -> ServerTags:
        """獲取伺服器標籤"""
        return await Database.select_one(ServerTags, ServerTags.server_id.is_(guild_id))
    
    
    @classmethod
    async def fill_missing_data(
        cls,
        user_id: int,  # 必填
        guild_id: int,  # 必填
        group: Optional[Group] = _UNSET,  # 可選
        user_record: Optional[UserRecord] = _UNSET,
        user_config: Optional[UserConfiguration] = _UNSET,
        server_config: Optional[ServerConfiguration] = _UNSET,
        server_tags: Optional[ServerTags] = _UNSET,
        black_list: Optional[BlackList] = _UNSET,
        white_list: Optional[WhiteList] = _UNSET
    ) -> FilledData:
        """主要入口方法"""
        resolved = {}
        
        # 處理每個可選參數
        for field, value in [
            ('group', group),  # 群組需要額外處理
            ('user_record', user_record),
            ('user_config', user_config),
            ('server_config', server_config),
            ('server_tags', server_tags),  # 伺服器標籤使用伺服器配置
            ('black_list', black_list),
            ('white_list', white_list)
        ]:
            if value is _UNSET:
                continue  # 跳過未傳入的參數
                
            resolved[field] = await cls._resolve_value(
                user_id=user_id,
                guild_id=guild_id,
                value=value,
                field_name=field
            )

        return FilledData(user_id=user_id, guild_id=guild_id, **resolved)
    
    @classmethod
    async def save_data(
        cls,
        group: Optional[Group] = _UNSET,
        user_record: Optional[UserRecord] = _UNSET,
        user_config: Optional[UserConfiguration] = _UNSET,
        server_config: Optional[ServerConfiguration] = _UNSET,
        server_tags: Optional[ServerConfiguration] = _UNSET,
    ) -> None:
        """通用儲存方法
        只儲存有傳入的參數，使用 insert_or_replace 操作
        """
        # 過濾掉未傳入的參數 (_UNSET)
        params = {
            'group': group,
            'user_record': user_record,
            'user_config': user_config,
            'server_config': server_config,
            'server_tags': server_tags
        }
        
        for name, value in params.items():
            if value is not _UNSET:
                await Database.insert_or_replace(value)


    @classmethod
    async def delete_data(
        cls,
        group: Optional[Group] = _UNSET,
        white_list: Optional[WhiteList] = _UNSET,
        black_list: Optional[BlackList] = _UNSET,
    ) -> None:

        # 過濾掉未傳入的參數 (_UNSET)
        params = {
            'group': group,
            'white_list': white_list,
            'black_list': black_list,
        }
        
        for name, value in params.items():
            if value is not _UNSET:
                await Database.delete_instance(value)