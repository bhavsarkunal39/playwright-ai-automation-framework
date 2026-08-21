import os
import re

def revert_locators_files(root_path):
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if filename == "locators.py":
                file_path = os.path.join(dirpath, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # Replace "..." with r'''...''' (for lines that look like XPath or selectors)
                # This assumes all double-quoted strings should be triple-quoted raw strings
                def replacer(match):
                    inner = match.group(1)
                    return f"r'''{inner}'''"
                # Only replace double-quoted strings that are not already triple-quoted
                content = re.sub(r'"([^"\n]*)"', replacer, content)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Reverted {file_path}")

# Example usage:
revert_locators_files(r"c:\Projects\PyBot\Object_Repository\PRA_Revera")