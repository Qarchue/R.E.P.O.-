import discord
from discord.ext import commands

from database import (
    Database, 
    User, 
    Group, 
    Server,
    UserRecord, 
    ServerTags, 
    UserConfiguration, 
    ServerConfiguration, 
)

from managers import GroupManager

from utility import LOG, config


class EventDatabase:
    def __init__(self):
        pass

    @staticmethod
    async def add_user(member: discord.Member) -> User | None:
        """
        增加使用者至資料表
        member: discord.Member
        """
        user = await Database.select_one(User, User.discord_id.is_(member.id))
        if user is None:
            user = User(member.id)
            user.name = member.name

            LOG.System(f"新增資料: {LOG.User(member)}")
            await Database.insert_or_replace(user)

            user_config = UserConfiguration(member.id)
            user_config.user = user
            user_config.group_password = None
            user_config.limit_mode = 0
            
            await Database.insert_or_replace(user_config)
            LOG.System(f"新增使用者設定資料: {LOG.User(member)}")

            user_record = UserRecord(member.id)
            user_record.user = user
            
            await Database.insert_or_replace(user_record)
            return user
        
    @staticmethod
    async def add_server(guild: discord.Guild) -> Server | None:
        """
        增加伺服器至資料表
        guild: discord.Guild
        """
        server = await Database.select_one(Server, Server.server_id.is_(guild.id))
        if server is None:
            server = Server(guild.id)
            server.name = guild.name


            await Database.insert_or_replace(server)
            LOG.System(f"新增資料: {LOG.Server(guild)}")


            server_config = ServerConfiguration(guild.id)
            server_config.server = server

            await Database.insert_or_replace(server_config)
            LOG.System(f"新增設定資料: {LOG.Server(guild)}")
            


            server_tags = ServerTags(guild.id)
            server_tags.server = server
            server_tags.versions= {}
            server_tags.custom_tags = {}
            await Database.insert_or_replace(server_tags)
            LOG.System(f"新增標籤資料: {LOG.Server(guild)}")
            return server
        

        
    @staticmethod
    async def group_check(bot: commands.Bot, guild: discord.Guild, group: Group) -> Group | None:
        """
        檢查群組的有效性，若無效則刪除相關資料，若有效則執行某個函式
        guild: discord.Guild
        group: Group
        """
        voice_channel = None
        thread = None

        try:
            # 檢查群組擁有者是否存在
            user = guild.get_member(group.owner_id)
            if user is None:
                raise ValueError("群組擁有者不存在")

            # 檢查語音頻道是否存在且有成員
            voice_channel = guild.get_channel(group.voice_channel_id)
            if voice_channel is None or len(voice_channel.members) == 0:
                raise ValueError("語音頻道不存在或無成員")

            # 檢查討論串是否存在且描述訊息有效
            thread = guild.get_thread(group.thread_id)
            if thread is None:
                raise ValueError("討論串不存在")
            await thread.fetch_message(group.description_message_id)

            # 如果檢查通過，執行某個函式
            await GroupManager.add_views(
                bot=bot,
                guild=guild,
                user=user,
                voice_channel=voice_channel,
            )
            LOG.System(f"群組檢查通過並執行函式: {LOG.User(group.owner_id)}")

        except Exception as e:
            LOG.System(f"檢查群組時發生錯誤: {e}")
            # 嘗試刪除無效的群組資料
            try:
                await GroupManager.delete(
                    guild=guild,
                    user_id=group.owner_id,
                    group=group,
                    voice_channel=voice_channel,
                    thread=thread,
                )
                LOG.System(f"已刪除無效的群組資料: {LOG.User(group.owner_id)}")
            except Exception as delete_error:
                LOG.System(f"刪除群組資料時發生錯誤: {delete_error}")

class EventManageCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot


    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await EventDatabase.add_user(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        pass

    @commands.Cog.listener()
    async def on_ready(self):


        for guild in self.bot.guilds:
            server = await Database.select_one(Server, Server.server_id.is_(guild.id))

            if server is None:
                await EventDatabase.add_server(guild)

            else:
                groups = await Database.select_all(Group, Group.server_id.is_(guild.id))
                for group in groups:
                    await EventDatabase.group_check(bot=self.bot, guild=guild, group=group)

                    
            for member in guild.members:
                try:
                    await EventDatabase.add_user(member)
                    
                except Exception as e:
                    LOG.System(f"錯誤{e}")




    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild | None):
        await EventDatabase.add_server(guild)
        for member in guild.members:
            try:
                await EventDatabase.add_user(member)
            except Exception as e:
                LOG.System(f"錯誤{e}")



    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild | None):
        server = await Database.select_one(Server, Server.server_id.is_(guild.id))
        if server is not None:
            await Database.delete(server)
            LOG.System(f"伺服器: {LOG.Server(guild)} 被移除")
        else:
            LOG.System(f"伺服器: {LOG.Server(guild)} 已經不存在")



    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        if before.name != after.name:
            server = await Database.select_one(Server, Server.server_id.is_(before.id))
            server.name = after.name
            LOG.System(f"伺服器: {LOG.Server(before)} 將名稱改成 {LOG.Server(after)}")
            await Database.insert_or_replace(server)


    




async def setup(client: commands.Bot):
    await client.add_cog(EventManageCog(client))
