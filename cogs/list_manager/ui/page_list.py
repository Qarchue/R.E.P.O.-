from typing import List, Optional

import discord
from discord.ui import Select, View

from datetime import datetime

from utility import config, LOG


class member_list():
    def __init__(
        self, 
        name: str,
        color: discord.Color, 
        show_when_empty: bool = False,
    ):
        self.name = name
        self.color = color
        self.list: list[discord.Member] = []
        self.show_when_empty = show_when_empty
        

    def add_member(self, member: discord.Member):
        self.list.append(member)

    def convert_to_embed(self, interaction: discord.Integration, title: str ) -> list[discord.Embed]:
        embeds: list[discord.Embed] = []
        embed_title = f"{title}-{self.name}"
        for i in range(0, len(self.list), 10):
            embed = discord.Embed(
                title=embed_title,
                description=f"顯示第 {i + 1} - {min(i + 10, len(self.list))} 筆",
                color=self.color,
                timestamp=datetime.now(),
            )
            # 添加每個申請表的信息到嵌入消息
            for j, member in enumerate(self.list[i:i + 10], start=i + 1):
                if member is None:
                    continue
                # 如果成員不存在，則跳過

                embed.add_field(
                    name=f"{j}. {member.display_name}",
                    value=f"  - {member.name}",
                    inline=False
                )
            
            embed.set_footer(
                text=f"總共 {len(self.list)} 筆",
                icon_url=interaction.guild.icon.url if interaction.guild.icon else None
            )
            embeds.append(embed)


        if len(embeds) == 0 and self.show_when_empty:
            embed = discord.Embed(
                title=embed_title,
                color=self.color,
                timestamp=datetime.now(),
            )
            embeds.append(discord.Embed(
                title=embed_title,
                description="這裡空空如也",
                color=self.color,
            ))
            

        return embeds
    


class AppNav(View):
    """
    用於控制菜單互動的實際 View 類別

    參數:
        pages (List[discord.Embed], optional): 要循環顯示的頁面列表。預設為 None。
        timeout (Optional[float], optional): 互動有效持續時間。預設為 None。
        ephemeral (Optional[bool], optional): 以短暫消息方式發送。預設為 False。
        allowed_user (Optional[discord.Member], optional): 允許進行互動的用戶。預設為 None。
    """

    index = 0  # 頁面索引
    switch_index = 0  # 切換頁面索引

    def __init__(
        self,
        embed_lists: List[List[discord.Embed]],
        timeout: Optional[float] = None,
    ):
        super().__init__(timeout=timeout)
        self.switch_count = len(embed_lists)
        if self.switch_count == 1:
            self.remove_item(self.switch_embeds)
        self.page_counts = [len(embed_list) for embed_list in embed_lists]  # 總頁數
        self.have_ui = True  # 是否有 UI

        self.embed_lists = embed_lists  # 嵌入消息列表


        self.get_current_page()  # 獲取當前頁面
        self.update_ui()  # 更新 UI

    def get_current_page(self):
        switch_index_incount = self.switch_index % self.switch_count
        self.page_count = self.page_counts[switch_index_incount]  # 總頁數
        index_incount = self.index % self.page_count  # 當前頁面索引
        self.pages = self.embed_lists[switch_index_incount]
        self.page = self.pages[index_incount]

    def update_ui(self):
        if self.page and len(self.pages) == 1:
            if self.have_ui:
                self.have_ui = False
                self.remove_item(self.previous)
                self.remove_item(self.next)
                self.remove_item(self.select)
        else:
            if not self.have_ui:
                self.have_ui = True
                self.add_item(self.previous)
                self.add_item(self.next)
                if self.select not in self.children:  # ✅ 避免重複 add
                    self.add_item(self.select)

        if self.page and len(self.pages) > 1:
            if self.select not in self.children:
                self.add_item(self.select)  # 再次防呆 ✅
            self.select.options.clear()  # ✅ 清空舊選項
            for index, page in enumerate(self.pages):
                self.select.add_option(
                    label=f"{page.title}",
                    description=f"{page.description[:96]}...".replace("`", ""),
                    value=index,
                )


    @discord.ui.button(
        label="上一頁",
        style=discord.ButtonStyle.success,
        row=1,
        custom_id="list_manager:previous",
    )
    async def previous(self, interaction: discord.Interaction, button: discord.Button):
        self.index -= 1  # 頁面索引減一
        await self.update(interaction)  # 更新頁面

    @discord.ui.button(
        label="下一頁",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="list_manager:next",
    )
    async def next(self, interaction: discord.Interaction, button: discord.Button):
        self.index += 1  # 頁面索引加一
        await self.update(interaction)  # 更新頁面

    @discord.ui.button(
        label="切換顯示",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="list_manager:switch_embeds",
    )
    async def switch_embeds(self, interaction: discord.Interaction, button: discord.Button):
        self.index = 0  # 重置頁面索引
        self.switch_index += 1  # 切換頁面索引加一
        self.get_current_page()  # 獲取當前頁面
        self.update_ui()  # 更新頁面
        await self.update(interaction)

    @discord.ui.select(row=2, custom_id="list_manager:select")
    async def select(self, interaction: discord.Interaction, select: Select):
        self.index = int(select.values[0])  # 設置頁面索引為選擇的值
        await self.update(interaction)  # 更新頁面

    async def update(self, interaction: discord.Interaction):
        self.get_current_page()  # 獲取當前頁面
        if self.page_count > 0:
            await interaction.response.edit_message(
                embed=self.page, view=self
            )  # 編輯消息以顯示當前頁面
        else:
            await interaction.response.send_message("沒有關聯的頁面可以顯示", ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # 如果沒有設置允許互動的用戶且是刪除操作，允許互動


class AppMenu():
    def __init__(
        self,
        timeout: Optional[float] = None,
    ) -> None:
        self.timeout = timeout

    async def send_pages(
        self,
        interaction: discord.Interaction,
        embed_lists: List[List[discord.Embed]],
    ):

        await interaction.followup.send(
            embed=embed_lists[0][0],
            view=AppNav(
                embed_lists=embed_lists,
                timeout=self.timeout,
            ),
        )




# 分頁顯示申請表
async def send_form_pages(
        interaction: discord.Interaction,
        title: str, 
        member_lists: List[member_list],

) -> None:
    """
    分頁顯示申請表，每 10 個為一頁。

    參數:
        interaction (discord.Interaction): Discord 的互動對象。
    """
    embed_lists = []
    for member_list1 in member_lists:
        converted = member_list1.convert_to_embed(interaction, title)
        if len(converted):   
            embed_lists.append(converted)
        

    # 使用類似於 AppMenu 的功能來分頁顯示
    app_menu = AppMenu(timeout=60.0)
    await app_menu.send_pages(interaction, embed_lists)
    
