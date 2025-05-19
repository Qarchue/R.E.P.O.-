import discord

from typing import Optional, Callable


import discord
from typing import List

class TagSelect(discord.ui.Select):
    def __init__(self, options: List[discord.SelectOption], on_select: Callable[[discord.Interaction, List[str]], None]):
        super().__init__(
            placeholder="請選擇標籤 (可多選)",
            min_values=1,
            max_values=len(options),
            options=options,
        )
        self.on_select = on_select

    async def callback(self, interaction: discord.Interaction):
        # 呼叫外部 callback 並傳遞選擇結果
        await self.on_select(interaction, self.values)

class TagSelectionView(discord.ui.View):
    def __init__(self, tag_options: List[dict], on_select: Callable[[discord.Interaction, List[str]], None]):
        super().__init__()
        options = [
            discord.SelectOption(label=tag["label"], value=tag["value"])
            for tag in tag_options
        ]
        self.add_item(TagSelect(options, on_select))

# 用法範例
# async def handle_select(interaction, values):
#     await interaction.response.send_message(f"你選擇了: {values}", ephemeral=True)
# view = TagSelectionView(tag_options, handle_select)
# await interaction.response.send_message(view=view)

