import discord
from typing import Optional
from datetime import datetime
import discord

class ThreadOperator:
    @staticmethod
    async def create(
        user: discord.User,
        forum: discord.ForumChannel,
        name: str,
        content: Optional[str] = None,
        avatar_file: Optional[discord.File] = None,
    ) -> discord.Thread:
        if content is None:
            timestamp = int(datetime.now().timestamp())
            content = f"房間創建時間: <t:{timestamp}:F>"

        if avatar_file is None:
            avatar_file = await user.display_avatar.to_file()

        thread = await forum.create_thread(
            name=name,
            content=content,
            file=avatar_file,
        )
        return thread.thread
    
    @staticmethod
    async def delete(
        thread: discord.Thread,
    ) -> None:
        if thread is None:
            return
        await thread.delete()


class ThreadEnsurer:
    @staticmethod
    async def ensure_thread(
        forum: discord.ForumChannel,
        thread_id: int | None,
        name: Optional[str] = None,
        content: Optional[str] = None,
    ) -> discord.Thread:
        thread = None
        if thread_id is not None:
            thread: discord.Thread = forum.get_thread(thread_id)
            if thread is None:
                thread = None
            else:
                try:
                    description = await thread.fetch_message(thread_id)
                except:
                    await thread.delete()
                    thread = None


        if thread is None:
            thread = await ThreadOperator.create(
                user=forum.guild.me,
                forum=forum,
                name=name if name is not None else "揪團論壇",
                content=content if content is not None else "使用這個頻道揪團",
            )
            return thread
        
        if name is not None and name != thread.name:
            await thread.edit(name=name)
        if content is not None and content != description.content:
            await description.edit(content=content)        
        return thread

class ThreadManager(ThreadOperator, ThreadEnsurer):
    
    @staticmethod
    async def update_thread(
        thread: discord.Thread,
        name: str,
        content: str,
    ) -> None:
        if thread is None:
            return
        await thread.edit(name=name)
        try:
            description_message = await thread.fetch_message(thread.id)
        except discord.NotFound:
            return
        await description_message.edit(content=content)