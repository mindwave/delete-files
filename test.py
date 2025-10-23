import os

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
                    file_info_list.append(directory_path + "/" + entry.name)
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

directory = '/home/mhulse/Documents/Testing'

class FileList():
    files_data = get_file_info(directory)
    if files_data:
        for file_data in files_data:
            print(f"File Name: {file_data}")

if __name__=="__main__":
  FileList()
