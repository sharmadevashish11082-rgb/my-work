import os
import shutil
import hashlib
from pathlib import Path

# Folder to organize
ROOT_FOLDER = r"C:\Users\aju12\Downloads"

# File categories
FILE_TYPES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov"],
    "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx"],
    "Archives": [".zip", ".rar", ".7z"],
    "Music": [".mp3", ".wav", ".flac"]
}


def get_file_hash(filepath):
    """Generate SHA256 hash of a file."""
    sha256 = hashlib.sha256()

    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(4096):
                sha256.update(chunk)

        return sha256.hexdigest()

    except Exception:
        return None


def organize_files(root_folder):
    print("\nOrganizing files...")

    for file in os.listdir(root_folder):
        file_path = os.path.join(root_folder, file)

        if not os.path.isfile(file_path):
            continue

        extension = Path(file).suffix.lower()

        moved = False

        for category, extensions in FILE_TYPES.items():
            if extension in extensions:
                destination = os.path.join(root_folder, category)
                os.makedirs(destination, exist_ok=True)

                shutil.move(
                    file_path,
                    os.path.join(destination, file)
                )

                moved = True
                break

        if not moved:
            destination = os.path.join(root_folder, "Others")
            os.makedirs(destination, exist_ok=True)

            shutil.move(
                file_path,
                os.path.join(destination, file)
            )

    print("Organization complete.")


def rename_files(root_folder):
    print("\nRenaming files...")

    for foldername, _, filenames in os.walk(root_folder):

        count = 1

        for filename in filenames:
            old_path = os.path.join(foldername, filename)

            extension = Path(filename).suffix

            new_name = f"file_{count:04d}{extension}"
            new_path = os.path.join(foldername, new_name)

            while os.path.exists(new_path):
                count += 1
                new_name = f"file_{count:04d}{extension}"
                new_path = os.path.join(foldername, new_name)

            os.rename(old_path, new_path)
            count += 1

    print("Renaming complete.")


def find_duplicates(root_folder):
    print("\nScanning for duplicates...")

    hashes = {}
    duplicates = []

    for foldername, _, filenames in os.walk(root_folder):

        for filename in filenames:
            filepath = os.path.join(foldername, filename)

            file_hash = get_file_hash(filepath)

            if not file_hash:
                continue

            if file_hash in hashes:
                duplicates.append(filepath)
            else:
                hashes[file_hash] = filepath

    if duplicates:
        print("\nDuplicates Found:")
        for dup in duplicates:
            print(dup)

    else:
        print("No duplicates found.")

    return duplicates


def delete_duplicates(duplicates):
    for file in duplicates:
        try:
            os.remove(file)
            print(f"Deleted: {file}")
        except Exception as e:
            print(f"Error deleting {file}: {e}")


if __name__ == "__main__":

    print(f"\nTarget Folder: {ROOT_FOLDER}")

    organize_files(ROOT_FOLDER)

    duplicates = find_duplicates(ROOT_FOLDER)

    choice = input(
        "\nDelete duplicate files? (y/n): "
    ).lower()

    if choice == "y":
        delete_duplicates(duplicates)

    rename_choice = input(
        "\nRename all files? (y/n): "
    ).lower()

    if rename_choice == "y":
        rename_files(ROOT_FOLDER)

    print("\nDone!")



    