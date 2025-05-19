import aiohttp
from .config import config

class steam_API:
    class SteamFriendCodeError(Exception): pass
    class InvalidAPIKeyError(SteamFriendCodeError): pass
    class UserNotFoundError(SteamFriendCodeError): pass
    class SteamAPIError(SteamFriendCodeError): pass
    class SteamNetworkError(SteamFriendCodeError): pass

    @staticmethod
    async def is_valid_steam_friend_code(friend_code: int, steamAPI_key: str) -> bool:
        steamid64 = friend_code + 76561197960265728
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steamAPI_key}&steamids={steamid64}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 403:
                        raise steam_API.InvalidAPIKeyError()
                    elif resp.status != 200:
                        raise steam_API.SteamAPIError()

                    data = await resp.json()

                    print(data)
                    players = data.get("response", {}).get("players")
                    if not players:
                        raise steam_API.UserNotFoundError()
                    return True

        except aiohttp.ClientError:
            raise steam_API.SteamNetworkError()
        


    @staticmethod
    async def verify_steam_api_key(steam_api_key: str) -> bool:
        # 使用 Valve 創辦人 Gabe 的公開 Steam ID 來驗證 API Key
        known_steamid64 = 76561197960287930  # 公開帳號，不涉及隱私

        url = (
            f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
            f"?key={steam_api_key}&steamids={known_steamid64}"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 403:
                        raise steam_API.InvalidAPIKeyError("無效的 Steam API 金鑰")
                    elif resp.status != 200:
                        raise steam_API.SteamAPIError(f"Steam API 錯誤: HTTP {resp.status}")

                    data = await resp.json()
                    if "players" in data.get("response", {}):
                        return True
                    else:
                        raise steam_API.SteamAPIError("API 回傳格式錯誤")

        except aiohttp.ClientError as e:
            raise steam_API.SteamNetworkError(f"網路錯誤: {e}")