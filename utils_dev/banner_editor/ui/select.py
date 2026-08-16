from __future__ import annotations
import logging


from discord.ui import Select
from discord import Interaction, SelectOption, Message
from typing import TYPE_CHECKING

from utils_dev.banner_editor.edited_banner import Edited_DB_Banner

from utils_dev.banner_editor.ui.modal import Banner_Modal
from core.utils_ui import banner_field_label

if TYPE_CHECKING:
    from core.AMP import AMPInstance
    from utils_dev.banner_editor.edited_banner import Edited_DB_Banner
    from utils_dev.banner_editor.ui.view import Banner_Editor_View


class Banner_Editor_Select(Select):
    def __init__(self, edited_db_banner: Edited_DB_Banner, view: Banner_Editor_View, amp_server: AMPInstance, banner_message: Message, custom_id: str | None = None, min_values: int = 1, max_values: int = 1, row: int | None = None, disabled: bool = False, placeholder: str | None = None):
        self.logger = logging.getLogger()
        options = []
        self._banner_view = view

        self._edited_db_banner = edited_db_banner
        self._banner_message = banner_message

        self._amp_server = amp_server

        whitelist_options = [
            SelectOption(label=banner_field_label('color_whitelist_open'), value='color_whitelist_open'),
            SelectOption(label=banner_field_label('color_whitelist_closed'), value='color_whitelist_closed')]
        donator_options = [
            SelectOption(label=banner_field_label('color_donator'), value='color_donator')]

        options = [
            SelectOption(label=banner_field_label('blur_background_amount'), value='blur_background_amount'),
            SelectOption(label=banner_field_label('color_header'), value='color_header'),
            SelectOption(label=banner_field_label('color_body'), value='color_body'),
            SelectOption(label=banner_field_label('color_host'), value='color_host'),

            SelectOption(label=banner_field_label('color_status_online'), value='color_status_online'),
            SelectOption(label=banner_field_label('color_status_offline'), value='color_status_offline'),
            SelectOption(label=banner_field_label('color_player_limit_min'), value='color_player_limit_min'),
            SelectOption(label=banner_field_label('color_player_limit_max'), value='color_player_limit_max'),
            SelectOption(label=banner_field_label('color_player_online'), value='color_player_online')
        ]

        # If Whitelist is disabled, remove the options from the list.
        if not self._amp_server.Whitelist_disabled:
            options = whitelist_options + options

        # If Donator Only is enabled; adds the option to set the color.
        if self._amp_server.Donator:
            options = options + donator_options

        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)

    async def callback(self, interaction: Interaction):
        if self.values[0] == 'blur_background_amount':
            input_type = 'int'
        else:
            input_type = 'color'

        self._banner_modal = Banner_Modal(input_type=input_type, title=banner_field_label(self.values[0]), select_value=self.values[0], edited_db_banner=self._edited_db_banner, banner_message=self._banner_message, view=self._banner_view, amp_server=self._amp_server)
        await interaction.response.send_modal(self._banner_modal)

        self._first_interaction = False
