import os
import re

def find_duplicate_keys_in_file(filepath):
    key_pattern = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=')
    keys_seen = {}
    duplicates = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            match = key_pattern.match(line.strip())
            if match:
                key = match.group(1).lower()  # case-insensitive
                if key in keys_seen:
                    duplicates.add((match.group(1), keys_seen[key], lineno))
                else:
                    keys_seen[key] = lineno
    return duplicates

def scan_directory_for_duplicates(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            filepath = os.path.join(directory, filename)
            duplicates = find_duplicate_keys_in_file(filepath)    
            if duplicates:
                #print(f'\nDuplicates in {filename}:')
                os.makedirs(duplicateF, exist_ok=True)
                filePath=os.path.join(duplicateF, 'duplicates.txt')         
                with open(filePath, 'a', encoding='utf-8') as dup_file:
                    dup_file.write(f"-------------Duplicates in {filename}:---------------\n")
                for key, first_line, dup_line in duplicates:
                    #print(f"  Key '{key}' at lines {first_line} and {dup_line}")
                    
                    with open(filePath, 'a', encoding='utf-8') as dup_file:
                        dup_file.write(f"Key '{key}' at lines {first_line} and {dup_line}\n")
                print()

if __name__ == '__main__':
    directory = r'c:\Projects\PyBot\Object_Repository\PRA_Revera'  # Change as needed
    duplicateF=r'c:\Projects\PyBot\Object_Repository\Duplicates'
    scan_directory_for_duplicates(directory)