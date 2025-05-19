import discord

class ForumOperator:
    @staticmethod
    async def create_forum(
        guild: discord.Guild,
        category: discord.CategoryChannel,
        channel_name: str,
    ) -> discord.ForumChannel:
        forum = await guild.create_forum(
            name=channel_name,
            category=category,
        )
        return forum

    @staticmethod
    async def delete_forum(
        forum: discord.ForumChannel
    ) -> None:
        if forum is not None:
            await forum.delete()


class ForumEnsurer:
    @staticmethod
    async def ensure_forum(
        guild: discord.Guild,
        channel_id: int | None,
        category: discord.CategoryChannel,
    ) -> discord.ForumChannel:
        forum = None
        if channel_id is not None:
            forum = guild.get_channel(channel_id)
        if forum is None:
            forum = await ForumOperator.create_forum(
                guild=guild,
                category=category,
                channel_name="揪團論壇",
            )
            return forum
        
        return forum



class ForumManager(ForumOperator, ForumEnsurer):
    pass

