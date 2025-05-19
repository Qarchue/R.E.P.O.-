from collections import defaultdict
import asyncio
import discord
from typing import Optional, Callable


class TimeoutOperation:
    # 用於追蹤語音頻道的計時任務
    voice_channel_tasks = defaultdict(lambda: None)

    @staticmethod
    async def start_timer(
        channel: discord.VoiceChannel,
        timeout: int,
        on_timeout: Callable[[], None],
    ):
        """
        啟動計時器，當計時結束後執行 `on_timeout`。

        :param channel: Discord 語音頻道
        :param timeout: 計時器的時間（秒）
        :param on_timeout: 計時結束後的回調函數
        """
        if TimeoutOperation.voice_channel_tasks[channel.id] is not None:
            # 如果已有計時器，直接返回
            return

        async def timer_task():
            try:
                await asyncio.sleep(timeout)  # 等待指定的時間
                if len(channel.members) == 0:  # 再次確認頻道是否沒人
                    try:
                        await on_timeout()
                    except Exception as e:
                        # 處理回調函數中的異常
                        print(f"Error in on_timeout: {e}")
            except asyncio.CancelledError:
                # 如果計時器被取消，直接退出
                pass
            finally:
                # 確保任務結束後清除記錄
                TimeoutOperation.voice_channel_tasks[channel.id] = None

        # 啟動計時器任務
        TimeoutOperation.voice_channel_tasks[channel.id] = asyncio.create_task(timer_task())

    @staticmethod
    async def cancel_timer(channel_id: int):
        """
        取消計時器。

        :param channel_id: 語音頻道的 ID
        """
        task = TimeoutOperation.voice_channel_tasks.get(channel_id)
        if task is not None:
            task.cancel()
            TimeoutOperation.voice_channel_tasks[channel_id] = None