import os
import datetime
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, Button, ListView, ListItem, Label
from textual.reactive import reactive

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
#directory = '/mnt/share/server-1'
directory = '/home/mhulse/Documents/Testing'

class FileList(App[None]):
  CSS_PATH = "checkbox.tcss"
  
  def compose(self) -> ComposeResult:
    files_data = reactive([])
    files_data = get_file_info(directory)
    yield ListView(
        # The * unpacks the list of files_data allowing each item
        # to be passed as individual arguments to the ListView
        *[ListItem(Checkbox(file, value=False, id=periodToUnderscore(file))) for file in files_data],
        id="checkbox_list"
    )
      
    yield Button("Delete Checked Items", id="get_checked_button")
      
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
                        # checked_items.append(self.query_one("#checkbox_list", ListView).index(checkbox.label))
                        # checked_items.append(index)
                        self.query_one("#checkbox_list", ListView).pop(index)
                        os.remove(directory + "/" + str(checkbox.label))

        # For testing...
        # self.notify won't show a list, has to be a str
        # for item in checked_items:
        #     checked_list += str(item) + " | "
        # self.notify(checked_list)


if __name__=="__main__":
  FileList().run()

