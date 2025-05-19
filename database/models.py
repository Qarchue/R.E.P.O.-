import sqlalchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship
from sqlalchemy import ForeignKey
from typing import List


class Base(MappedAsDataclass, DeclarativeBase):
    """資料庫 Table 基礎類別"""
    type_annotation_map = {dict[str, str]: sqlalchemy.JSON}


class WhiteList(Base):
    __tablename__ = "white_list"


    discord_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), primary_key=True)
    """白名單 Discord ID"""

    user_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), nullable=False)
    """對應使用者 Discord ID"""


class BlackList(Base):
    __tablename__ = "black_list"


    discord_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), primary_key=True)
    """黑名單 Discord ID"""

    user_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), nullable=False)
    """對應使用者 Discord ID"""


class Group(Base):
    __tablename__ = "group"


    owner_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), primary_key=True, nullable=False)
    """伺服器 ID"""

    server_id: Mapped[int] = mapped_column(ForeignKey("servers.server_id"), primary_key=True, nullable=False)
    """伺服器 ID"""

    voice_channel_id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    """語音頻道 ID"""

    thread_id: Mapped[int] = mapped_column(nullable=False)
    """揪團貼文 ID"""

    description_message_id: Mapped[int] = mapped_column(nullable=False)

class ServerTags(Base):
    __tablename__ = "server_tags"


    server_id: Mapped[int] = mapped_column(ForeignKey("servers.server_id"), primary_key=True)
    """伺服器 ID"""

    no_mods: Mapped[int] = mapped_column(default=None, nullable=True)
    """無模組"""

    custom_tags: Mapped[dict[str, int]] = mapped_column(sqlalchemy.JSON, default=None, nullable=True)
    """自訂標籤"""
    
    versions: Mapped[dict[str, int]] = mapped_column(sqlalchemy.JSON, default=None, nullable=True)
    """各版本"""

    server = relationship("Server", back_populates="tags")
    """對應的伺服器資料"""

class ServerConfiguration(Base):
    __tablename__ = "server_configuration"


    server_id: Mapped[int] = mapped_column(ForeignKey("servers.server_id"), primary_key=True)
    """伺服器 ID"""

    looking_for_group_channel: Mapped[int] = mapped_column(default=None, nullable=True)
    """揪團頻道 ID"""

    thread_id: Mapped[int] = mapped_column(default=None, nullable=True)
    """揪團主題 ID"""

    create_group_button: Mapped[int] = mapped_column(default=None, nullable=True)
    """揪團按鈕 ID"""      

    waiting_room_channel: Mapped[int] = mapped_column(default=None, nullable=True)
    """待機頻道 ID"""

    steamAPI_key: Mapped[str | None] = mapped_column(default=None, nullable=True)

    server = relationship("Server", back_populates="configuration")
    """對應的伺服器資料"""


class Server(Base):
    __tablename__ = "servers"


    server_id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    """伺服器 ID"""

    name: Mapped[str | None] = mapped_column(default=None)
    """伺服器名稱"""
    
    configuration = relationship("ServerConfiguration", back_populates="server", uselist=False)
    """伺服器設定資料"""

    tags = relationship("ServerTags", back_populates="server", uselist=False)
    """伺服器標籤資料"""


class UserConfiguration(Base):
    __tablename__ = "user_configuration"

    discord_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), primary_key=True)
    """使用者 Discord ID"""

    user = relationship("User", back_populates="configuration")
    """對應的使用者資料"""

    group_password: Mapped[str] = mapped_column(default=None, nullable=True)
    """房間加入密碼"""
    
    steam_friend_code: Mapped[str | None] = mapped_column(default=None)
    """Steam 好友代碼"""

    limit_mode: Mapped[int] = mapped_column(default=0)
    """限制模式"""

    user_limit: Mapped[int] = mapped_column(default=0)
    """限制模式"""


class UserRecord(Base):
    __tablename__ = "user_record"

    discord_id: Mapped[int] = mapped_column(ForeignKey("users.discord_id"), primary_key=True)
    """使用者 Discord ID"""

    user = relationship("User", back_populates="record")
    """對應的使用者資料"""

    voice_name: Mapped[str] = mapped_column(default=None, nullable=True)
    """揪團語音名稱"""
    
    group_name: Mapped[str] = mapped_column(default=None, nullable=True)
    """揪團名稱"""

    group_description: Mapped[str] = mapped_column(default=None, nullable=True)
    """揪團備註"""

    mod_code: Mapped[str] = mapped_column(default=None, nullable=True)
    """模組碼"""

    game_password: Mapped[str] = mapped_column(default=None, nullable=True)
    """遊戲內房間密碼"""
    
    create_count: Mapped[str] = mapped_column(default=0)
    """創立次數"""


class User(Base):
    __tablename__ = "users"


    discord_id: Mapped[int] = mapped_column(primary_key=True, unique=True, nullable=False)
    """使用者 Discord ID"""
   
    name: Mapped[str | None] = mapped_column(default=None)
    """使用者名稱"""

    configuration = relationship("UserConfiguration", back_populates="user", uselist=False)
    """使用者設定資料"""

    record = relationship("UserRecord", back_populates="user", uselist=False)
    """使用者設定資料"""