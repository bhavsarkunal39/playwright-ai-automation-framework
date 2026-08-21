import os
import re

def sanitize_dir_name(name):
    # Keep only alphanumeric and underscores, replace others with underscore
    return re.sub(r'[^A-Za-z0-9_]', '_', name.replace(' ', '_'))

def rename_and_sanitize_dirs(base_path):
    for root, dirs, files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            sanitized_name = sanitize_dir_name(dir_name)
            if dir_name != sanitized_name:
                old_path = os.path.join(root, dir_name)
                new_path = os.path.join(root, sanitized_name)
                # Avoid overwriting existing directories
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} -> {new_path}")
                else:
                    print(f"Skipped (target exists): {old_path} -> {new_path}")

if __name__ == "__main__":
    # Set your base path here
    base_path = r'Object_Repository/PRA_Revera'  # Change as needed
    rename_and_sanitize_dirs(base_path)