import os
import datetime
from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Grid
from textual.widgets import Checkbox, Button, ListView, ListItem, Label, Header, Footer
from textual.reactive import reactive
from textual.screen import ModalScreen

def periodToUnderscore(filename):
    return filename.replace(".", "__")

def underscoreToPeriod(filename):
    return filename.replace("__", ".")

def get_file_info(directory_path):
    """
    Retrieves information (name, size, modified date) for files in a given directory.

    Args:
        directory_path (str): The path to the directory.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              'name', 'size_bytes', and 'modified_date' for a file.
    """
    file_info_list = []
    try:
        #-------------------------
        # Just get the file names
        # ------------------------
        for entry in os.scandir(directory_path):
            if entry.is_file():
                try:
                    file_info_list.append(entry.name)
                except OSError as e:
                    print(f"Error accessing stats for {entry}: {e}")
        # ---------------------------
        # Get File Details
        # ----------------------------
        # for entry in os.scandir(directory_path):
        #     if entry.is_file():
        #         try:
        #             stats = entry.stat()
        #             file_info = {
        #                 'name': entry.name,
        #                 'size_bytes': stats.st_size,
        #                 'modified_date': datetime.datetime.fromtimestamp(stats.st_mtime)
        #             }
        #             file_info_list.append(file_info)
        #         except OSError as e:
        #             print(f"Error accessing stats for {entry.path}: {e}")
    except FileNotFoundError:
        print(f"Error: Directory not found at '{directory_path}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return file_info_list

# Example usage:
directory = '/mnt/share/server-1'
#directory = '/home/mhulse/Documents/Testing'

class ModalConfirm(ModalScreen):
    BINDINGS = [("escape", "app.pop_screen", "Pop screen")]
    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to delete these files?", id="confirm"),
            Button("YES", variant="error", id="confirm_delete"),
            Button("NO", variant="primary", id="cancel_delete"),
            id="modal_confirm"
        )

    def on_button_pressed(self, event:Button.Pressed) -> None:
        if event.button.id == "confirm_delete":
            self.app.pop_screen()
        if event.button.id == "cancel_delete":
            #self.notify("Button pushed")
            self.app.pop_screen()


class FileList(App[None]):
  CSS_PATH = "checkbox.tcss"
  
  def compose(self) -> ComposeResult:
    files_data = reactive([])
    files_data = get_file_info(directory)
    yield Header(show_clock=True)
    yield ListView(
        # The * unpacks the list of files_data allowing each item
        # to be passed as individual arguments to the ListView
        *[ListItem(Checkbox(file, value=False, id=periodToUnderscore(file))) for file in files_data],
        id="checkbox_list"
    )
    yield Footer()
      
    yield Button("Delete Checked Items", id="get_checked_button", variant="error")
    yield Button("Test Modal", id="show_modal", variant="primary")
      
  def on_button_pressed(self, event:Button.Pressed) -> None:
    if event.button.id == "get_checked_button":
        checked_items = []
        checked_list = ""

        list_of_checkboxes = self.query_one("#checkbox_list", ListView)

        # You have to use enumerate (apparently) to get the index
        # The index is need to pop the item off the ListView and
        # have the UI automatically refresh
        for index, list_item in enumerate(list_of_checkboxes.children):
            if isinstance(list_item, ListItem):
                for checkbox in list_item.query(Checkbox):
                    if checkbox.value:
                        self.query_one("#checkbox_list", ListView).pop(index)
                        os.remove(directory + "/" + str(checkbox.label))

        # For testing...
        # self.notify won't show a list, has to be a str
        # for item in checked_items:
        #     checked_list += str(item) + " | "
        # self.notify(checked_list)
    
    if event.button.id == "show_modal":
        self.app.push_screen(ModalConfirm())


if __name__=="__main__":
  FileList().run()

