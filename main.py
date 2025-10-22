import os
import datetime
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, Button

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
        for entry in os.scandir(directory_path):
            if entry.is_file():
                try:
                    stats = entry.stat()
                    file_info = {
                        'name': entry.name,
                        'size_bytes': stats.st_size,
                        'modified_date': datetime.datetime.fromtimestamp(stats.st_mtime)
                    }
                    file_info_list.append(file_info)
                except OSError as e:
                    print(f"Error accessing stats for {entry.path}: {e}")
    except FileNotFoundError:
        print(f"Error: Directory not found at '{directory_path}'")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return file_info_list

# Example usage:
directory = '/mnt/share/server-1'  # Current directory

class FileList(App[None]):
  CSS_PATH = "checkbox.tcss"
  
  def compose(self) -> ComposeResult:
    files_data = get_file_info(directory)
    with VerticalScroll(id="checkbox_container"):
      if files_data:
        for file_data in files_data:
          #yield Checkbox(file_data['name'] + " " + file_data['modified_date'].strftime("%Y-%m-%d %H:%M:%S") + " " + str(file_data['size_bytes']))
          yield Checkbox(file_data['name'])
    yield Button("Get Checked Items", id="get_checked_button")
      
  def on_button_pressed(self, event:Button.Pressed) -> None:
    if event.button.id == "get_checked_button":
        checked_items = []
        checked_list = ""
        for checkbox in self.query_one("#checkbox_container").children:
            if isinstance(checkbox, Checkbox) and checkbox.value:
                checked_items.append(checkbox.label)

        # self.notify won't show a list, has to be a str
        for item in checked_items:
            checked_list += str(item) + " | "

        self.notify(checked_list)


if __name__=="__main__":
  FileList().run()

