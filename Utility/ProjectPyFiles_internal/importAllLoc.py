import os

def find_locators_files(base_path, import_prefix):
    import_lines = []
    for root, dirs, files in os.walk(base_path):
        if 'locators.py' in files:
            # Get the relative path from the base_path to the directory containing locators.py
            rel_path = os.path.relpath(root, base_path)
            # Replace OS-specific path separators with dots for Python import
            if rel_path == '.':
                module_path = ''
            else:
                module_path = '.' + rel_path.replace(os.sep, '.')
            import_line = f"import {import_prefix}{module_path}.locators"
            import_lines.append(import_line)
    return import_lines

if __name__ == "__main__":
    # Set your base path and import prefix here
    base_path = os.path.join('Object_Repository', 'PRA_Revera')
    import_prefix = 'Object_Repository.PRA_Revera'
    imports = find_locators_files(base_path, import_prefix)
    with open('mainlocator.py', 'w') as f:
        for line in imports:
            f.write(line + '\n')
    print(f"Generated {len(imports)} import statements in mainlocator.py")