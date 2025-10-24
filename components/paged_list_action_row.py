from discord import ui, ButtonStyle
from typing import Callable, Any
from main import *


class InvalidPageError(Exception):
    def __init__(
        self,
        max_page: int,
        page: int,
    ):
        """Exception raised when an invalid page number is requested."""
        super().__init__(
            f"Page number {page} is invalid. Must be between 1 and {max_page}."
        )
        self.max_page = max_page
        self.page = page


class SpecificPageModal(ui.Modal, title="Go to Page"):
    page_input = ui.Label(text="Page number", component=ui.TextInput())

    def __init__(self, action_row: "PagedListActionRow", max_page: int):
        super().__init__()
        assert isinstance(self.page_input.component, ui.TextInput)
        self.action_row = action_row
        self.page_input.component.placeholder = str(action_row._current_page)
        self.page_input.component.max_length = len(str(max_page))

    async def on_submit(self, interaction: discord.Interaction):
        assert isinstance(self.page_input.component, ui.TextInput)
        try:
            requested_page = int(self.page_input.component.value)
            total_items, total_pages, start_index, stop_index = (
                self.action_row._get_pages_info(requested_page)
            )
            self.action_row._edit_buttons_state(requested_page, total_pages)
            page_data = self.action_row.apply_page(
                start_index,
                stop_index,
                total_pages > 1,
                requested_page,
                total_items,
                total_pages,
            )
            self.action_row._current_page = requested_page
            await self.action_row.responde_to_interaction(interaction, page_data)
        except ValueError:
            await interaction.response.send_message(
                "Page number must be a positive integer", ephemeral=True
            )
        except InvalidPageError as e:
            await interaction.response.send_message(
                f"Page number must be between 1 and {e.max_page}",
                ephemeral=True,
            )


class PagedListActionRow(ui.ActionRow):
    def __init__(
        self,
        list_len_func: Callable[[], int],
        items_per_page: int,
        current_page: int = 1,
        button_style: ButtonStyle = ButtonStyle.gray,
    ):
        """Note: This calls apply_page once during initialization to set up initial page data."""
        super().__init__()
        self.list_len_func = list_len_func
        self.items_per_page = items_per_page
        self._current_page = current_page

        self._first_page_button.style = button_style
        self._previous_page_button.style = button_style
        self._current_page_button.style = button_style
        self._next_page_button.style = button_style
        self._last_page_button.style = button_style

        total_items, total_pages, start_index, stop_index = self._get_pages_info(
            current_page
        )
        self._edit_buttons_state(current_page, total_pages)
        self.init_page_data = self.apply_page(
            start_index,
            stop_index,
            total_pages > 1,
            current_page,
            total_items,
            total_pages,
        )

    def _get_pages_info(self, page: int) -> tuple[int, int, int, int]:
        """Returns: (total_items, total_pages, start_index, stop_index)"""
        total_items = self.list_len_func()
        if total_items == 0:
            return 0, 0, 0, 0
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        if not 1 <= page <= total_pages:
            raise InvalidPageError(total_pages, page)
        start_index = (page - 1) * self.items_per_page
        stop_index = min(start_index + self.items_per_page, total_items)
        return total_items, total_pages, start_index, stop_index

    def _edit_buttons_state(self, current_page: int, total_pages: int):
        self._first_page_button.disabled = current_page <= 1
        self._previous_page_button.disabled = current_page <= 1
        self._current_page_button.disabled = total_pages <= 1
        self._next_page_button.disabled = current_page >= total_pages
        self._last_page_button.disabled = current_page >= total_pages

        self._current_page_button.label = str(current_page)
        self._last_page_button.label = str(total_pages)

    def get_buttons(self) -> list[ui.Button]:
        """Returns the list of buttons in the action row."""
        return [
            self._first_page_button,
            self._previous_page_button,
            self._current_page_button,
            self._next_page_button,
            self._last_page_button,
        ]

    def apply_page(
        self,
        start_index: int,
        stop_index: int,
        multiple_pages: bool,
        page: int,
        total_items: int,
        total_pages: int,
    ) -> Any:
        """This will be called when the current page changes to apply the new page data."""
        pass

    async def responde_to_interaction(
        self, interaction: discord.Interaction, page_data: Any
    ) -> None:
        """Handles interaction responses. page_data is the result of apply_page."""
        pass

    @ui.button(label="1")
    async def _first_page_button(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        try:
            total_items, total_pages, start_index, stop_index = self._get_pages_info(1)
            self._edit_buttons_state(1, total_pages)
            page_data = self.apply_page(
                start_index,
                stop_index,
                total_pages > 1,
                1,
                total_items,
                total_pages,
            )
            self._current_page = 1
            await self.responde_to_interaction(interaction, page_data)
        except InvalidPageError as e:
            await interaction.response.send_message(
                f"Page number must be between 1 and {e.max_page}", ephemeral=True
            )

    @ui.button(label="<")
    async def _previous_page_button(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        try:
            new_page = self._current_page - 1
            total_items, total_pages, start_index, stop_index = self._get_pages_info(
                new_page
            )
            self._edit_buttons_state(new_page, total_pages)
            page_data = self.apply_page(
                start_index,
                stop_index,
                total_pages > 1,
                new_page,
                total_items,
                total_pages,
            )
            self._current_page = new_page
            await self.responde_to_interaction(interaction, page_data)
        except InvalidPageError as e:
            await interaction.response.send_message(
                f"Page number must be between 1 and {e.max_page}", ephemeral=True
            )

    @ui.button()
    async def _current_page_button(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        await interaction.response.send_modal(
            SpecificPageModal(self, int(self._last_page_button.label))
        )

    @ui.button(label=">")
    async def _next_page_button(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        try:
            new_page = self._current_page + 1
            total_items, total_pages, start_index, stop_index = self._get_pages_info(
                new_page
            )
            self._edit_buttons_state(new_page, total_pages)
            page_data = self.apply_page(
                start_index,
                stop_index,
                total_pages > 1,
                new_page,
                total_items,
                total_pages,
            )
            self._current_page = new_page
            await self.responde_to_interaction(interaction, page_data)
        except InvalidPageError as e:
            await interaction.response.send_message(
                f"Page number must be between 1 and {e.max_page}", ephemeral=True
            )

    @ui.button()
    async def _last_page_button(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        try:
            total_items, total_pages, start_index, stop_index = self._get_pages_info(
                int(button.label)
            )
            self._edit_buttons_state(total_pages, total_pages)
            page_data = self.apply_page(
                start_index,
                stop_index,
                total_pages > 1,
                total_pages,
                total_items,
                total_pages,
            )
            self._current_page = total_pages
            await self.responde_to_interaction(interaction, page_data)
        except InvalidPageError as e:
            await interaction.response.send_message(
                f"Page number must be between 1 and {e.max_page}", ephemeral=True
            )
