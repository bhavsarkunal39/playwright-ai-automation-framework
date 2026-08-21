import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import shutil

ROOT_DIR = r"c:\Kunal_gitRepo\revera-qa-repo\Object Repository\PRA Revera"
OUTPUT_ROOT = r"C:\Kunal Bhavsar\Migrated_Locators\PRA_Revera"  # <-- Set your external output path here

def extract_xpath_from_rs(rs_file):
    try:
        tree = ET.parse(rs_file)
        root = tree.getroot()
        name = root.findtext('name')
        for entry in root.findall(".//entry"):
            key = entry.findtext('key')
            if key == 'XPATH':
                value = entry.findtext('value')
                if value:
                    return name, value
    except Exception:
        pass
    return None, None

def collect_locators(root_dir):
    folder_locators = defaultdict(list)
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.rs'):
                full_path = os.path.join(dirpath, filename)
                name, xpath = extract_xpath_from_rs(full_path)
                if name and xpath:
                    folder_locators[dirpath].append((name, xpath))
    return folder_locators

def write_locators_py(folder_locators, root_dir, output_root):
    for folder, locators in folder_locators.items():
        # Compute relative path from root_dir
        rel_path = os.path.relpath(folder, root_dir)
        print(f'folder: {folder}')
        print(f'root_dir: {root_dir}')
        print(f'Rel path: {rel_path}')
        print(f'output_root: {output_root}')
        output_folder = os.path.join(output_root, rel_path)
        print(f'Output folder: {output_folder}')
        os.makedirs(output_folder, exist_ok=True)
        py_file = os.path.join(output_folder, 'locators.py')
        with open(py_file, 'w', encoding='utf-8') as f:
            f.write("# Auto-generated locators from .rs files\n\n")
            for name, xpath in locators:
                safe_name = name.replace(' ', '_').replace('-', '_')
                f.write(f"{safe_name} = r'''{xpath}'''\n")

if __name__ == "__main__":
    # Optional: clear output directory before writing
    if os.path.exists(OUTPUT_ROOT):
        shutil.rmtree(OUTPUT_ROOT)
    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    folder_locators = collect_locators(ROOT_DIR)
    write_locators_py(folder_locators, ROOT_DIR, OUTPUT_ROOT)
    print("Locator extraction and folder structure creation complete.")