from __future__ import annotations
import re
from typing import TYPE_CHECKING

from discord.ui import TextInput
from discord import TextStyle

from core import i18n

if TYPE_CHECKING:
    from utils_dev.banner_editor.ui.view import Banner_Editor_View
    from utils_dev.banner_editor.edited_banner import Edited_DB_Banner


class Copy_To_TextInput(TextInput):
    """This is used for Banner Editor View with the Copy To Button."""

    def __init__(self, style: TextStyle = TextStyle.short, required: bool = True, placeholder: str | None = None) -> None:
        placeholder = placeholder or i18n.t('ui.banner_copy.textinput_placeholder')
        label: str = i18n.t('ui.banner_copy.textinput_label')
        TextInput.__init__(self, label=label, style=style, required=required, placeholder=placeholder)


class Banner_Color_Input(TextInput):
    # This is the Modal that appears when Inputing a color hexcode.
    def __init__(self, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, select_value: str, label: str | None = None, style=TextStyle.short, placeholder: str = '#000000', default: str = '#ffffff', required=True, min_length=3, max_length=8):
        label = label or i18n.t('ui.banner_color_input.label')
        self._edited_db_banner = edited_db_banner
        self._select_value = select_value
        self._banner_view = view
        super().__init__(label=label, style=style, placeholder=placeholder, default=default, required=required, min_length=min_length, max_length=max_length)

    async def callback(self):
        # Remove the Hex code for validation.
        # Also lower the value for better comparison.
        self._value = self.value.lower()
        if self._value[0] == '#':
            self._value = self._value[1:]

        # Validate if Hex Color Code.
        if len(self._value) in [3, 4, 6, 8] and re.search(f'([0-9a-f]{{{len(self._value)}}})$', self._value):
            self._banner_view._logger.dev(f'Set attr for {self._edited_db_banner} {self._select_value} #{self._value}')
            setattr(self._edited_db_banner, self._select_value, '#' + self._value)
            return True

        else:
            return False


class Banner_Blur_Input(TextInput):
    # This is the Modal that appears when inputing the blur value.
    def __init__(self, view: Banner_Editor_View, edited_db_banner: Edited_DB_Banner, select_value: str, label: str | None = None, style=TextStyle.short, placeholder: str | None = None, default: int = 2, required=True, min_length=1, max_length=2):
        label = label or i18n.t('ui.banner_editor.fields.blur_background')
        placeholder = placeholder or i18n.t('ui.banner_blur_input.placeholder')
        self._edited_db_banner = edited_db_banner
        self._select_value = select_value
        self._banner_view = view
        super().__init__(label=label, style=style, placeholder=placeholder, default=default, required=required, min_length=min_length, max_length=max_length)

    async def callback(self):
        if self.value.isnumeric() and int(self.value) <= 99:
            self._banner_view._logger.dev(f'Set attr for {self._edited_db_banner} {self._select_value} {self.value}')
            setattr(self._edited_db_banner, self._select_value, int(self.value[0]))
            return True
        else:
            return False
