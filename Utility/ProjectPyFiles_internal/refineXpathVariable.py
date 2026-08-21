import os
import re

def sanitize_key(key, style='underscore'):
    if style == 'underscore':
        # Replace spaces and special characters with underscores
        return re.sub(r'\W+', '_', key.strip())
    elif style == 'camel':
        # Remove special characters, convert to camelCase
        parts = re.split(r'\W+', key.strip())
        return parts[0] + ''.join(word.capitalize() for word in parts[1:])
    else:
        raise ValueError("Unknown style: choose 'underscore' or 'camel'")

def process_locators_file(file_path, style='underscore'):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    # Match lines like: key = value, where key may have spaces/special chars
    pattern = re.compile(r'^(\s*)([^\s=][^=]*[^\s=])\s*=\s*(.+)$')
    for line in lines:
        match = pattern.match(line)
        if match:
            indent, key, value = match.groups()
            new_key = sanitize_key(key, style)
            new_line = f"{indent}{new_key} = {value}\n"
            new_lines.append(new_line)
        else:
            new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

def process_all_locators(base_path, style='underscore'):
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file == 'locators.py':
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                process_locators_file(file_path, style)

if __name__ == "__main__":
    # Set your base path here
    base_path = r'Object_Repository\PRA_Revera'  # Change as needed
    # Choose 'underscore' or 'camel'
    process_all_locators(base_path, style='underscore')