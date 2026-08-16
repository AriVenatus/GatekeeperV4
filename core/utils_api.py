# Copyright (C) 2021-2022 Katelynn Cadwallader
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations
import json
import re
import requests
from typing import Union


class GameAPIMixin():
    """Mojang/Steam profile lookup helpers, mixed into `botUtils` (see `core/utils.py`).

    Relies on `self.logger` and `self.AMPHandler` being set by `botUtils.__init__`.
    """

    def name_to_uuid_MC(self, name) -> Union[None, str]:
        """Converts an IGN to a UUID/Name Table
        `returns 'uuid'` else returns `None`, multiple results return `None`"""
        url = 'https://api.mojang.com/profiles/minecraft'
        header = {'Content-Type': 'application/json'}
        jsonhandler = json.dumps(name)
        post_req = requests.post(url, headers=header, data=jsonhandler)
        minecraft_user = post_req.json()

        if len(minecraft_user) == 0:
            return None

        if len(minecraft_user) > 1:
            return None

        else:
            return minecraft_user[0]['id']  # returns [{'id': 'uuid', 'name': 'name'}]

    def get_minecraft_profile(self, username: str) -> Union[dict, None]:
        """Resolves a Minecraft in-game name into profile info via the official Mojang API.
        Returns `{'name': str, 'uuid': str, 'avatar': str}` (`uuid` is undashed, matching `DBUser.MC_UUID`) or `None` if not found/failed."""
        try:
            req = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{username}', timeout=10)
        except Exception:
            self.logger.error('Mojang Profile Lookup request failed.', exc_info=True)
            return None

        if req.status_code != 200:
            return None

        data = req.json()
        uuid = data.get('id')
        name = data.get('name')
        if not uuid or not name:
            return None

        return {'name': name, 'uuid': uuid, 'avatar': f'https://mc-heads.net/avatar/{uuid}/100'}

    def name_to_steam_id(self, steamname: str) -> Union[None, str]:
        """Converts a Steam Name to a Steam ID returns `STEAM_0:0:2806383`
        """
        # Really basic HTML text scan to find the Title; which has the steam ID in it. Thank you STEAMIDFINDER! <3
        # <title> Steam ID STEAM_0:0:2806383 via Steam ID Finder</title>
        r = requests.get(f'https://www.steamidfinder.com/lookup/{steamname}')
        self.logger.dev('Status Code', r.status_code)
        if r.status_code == 404:
            return None

        title = re.search('(<title>)', r.text)
        start, title_start = title.span()
        title = re.search('(</title>)', r.text)
        title_end, end = title.span()
        # turns into  " STEAM_0:0:2806383 "
        # This should work regardless of the Steam ID length; since we came from the end of the second title backwards.
        steam_id = r.text[title_start + 9:title_end - 20].strip()
        self.logger.dev(f'Found Steam ID {steam_id}')
        return steam_id

    def steam_api_key_configured(self) -> bool:
        """Returns `True` if a Steam Web API Key has been set via GATEKEEPER_STEAM_API_KEY"""
        return bool(getattr(self.AMPHandler.tokens, 'SteamAPIKey', ''))

    def parse_steam_input(self, steam_input: str) -> tuple[str, bool]:
        """Parses a raw SteamID64, a full profile URL (`/profiles/<id>` or `/id/<vanity>`), or a bare vanity name.
        Returns `(value, is_steamid64)`"""
        steam_input = steam_input.strip()

        url_match = re.search(r'steamcommunity\.com/(profiles|id)/([^/\s]+)', steam_input, re.IGNORECASE)
        if url_match:
            kind, value = url_match.group(1).lower(), url_match.group(2)
            if kind == 'profiles' and value.isdigit():
                return value, True
            return value, False

        if steam_input.isdigit() and len(steam_input) == 17:
            return steam_input, True

        return steam_input, False

    def get_steam_profile(self, steam_input: str) -> Union[dict, None]:
        """Resolves a SteamID64, profile URL, or vanity name into Steam profile info via the Steam Web API.
        Requires `tokens.SteamAPIKey` to be set.
        Returns `{'steamid': str, 'personaname': str, 'avatar': str, 'profileurl': str}` or `None` if not found/unconfigured/failed."""
        api_key = getattr(self.AMPHandler.tokens, 'SteamAPIKey', '')
        if not api_key:
            return None

        steamid64, is_steamid64 = self.parse_steam_input(steam_input)

        if not is_steamid64:
            try:
                resolve_req = requests.get('https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/', params={'key': api_key, 'vanityurl': steamid64}, timeout=10)
                resolve_data = resolve_req.json().get('response', {})
            except Exception:
                self.logger.error('Steam ResolveVanityURL request failed.', exc_info=True)
                return None

            if resolve_data.get('success') != 1:
                return None

            steamid64 = resolve_data.get('steamid')

        try:
            summary_req = requests.get('https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/', params={'key': api_key, 'steamids': steamid64}, timeout=10)
            players = summary_req.json().get('response', {}).get('players', [])
        except Exception:
            self.logger.error('Steam GetPlayerSummaries request failed.', exc_info=True)
            return None

        if not len(players):
            return None

        player = players[0]
        return {'steamid': player.get('steamid'), 'personaname': player.get('personaname'), 'avatar': player.get('avatarfull'), 'profileurl': player.get('profileurl')}
