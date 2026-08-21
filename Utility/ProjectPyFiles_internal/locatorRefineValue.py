import os
import re

def fix_locators_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace r'''...''' or r"""...""" or '''...''' or """...""" with appropriate quotes
    def triple_quote_replacer(match):
        inner = match.group(3)
        # Prefer single quotes outside if double quotes inside, and vice versa
        if '"' in inner and "'" not in inner:
            return f"'{inner}'"
        elif "'" in inner and '"' not in inner:
            return f'"{inner}"'
        elif '"' in inner and "'" in inner:
            # Escape double quotes inside and use double quotes outside
            escaped = inner.replace('"', r'\"')
            return f'"{escaped}"'
        else:
            return f'"{inner}"'

    triple_pattern = re.compile(r"(r?)('''|\"\"\")(.*?)(\2)", re.DOTALL)
    content = triple_pattern.sub(triple_quote_replacer, content)

    # Replace r"..." or r'...' with "..." or '...'
    def raw_quote_replacer(match):
        quote = match.group(2)
        inner = match.group(3)
        return f"{quote}{inner}{quote}"

    raw_pattern = re.compile(r"r([\"'])(.*?)(\1)", re.DOTALL)
    content = raw_pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(1)}", content)

    # Fix any \" inside double-quoted strings by switching to single quotes if possible
    def fix_quotes(line):
        # Only process lines with = and a quoted string
        m = re.match(r"(\s*\w+\s*=\s*)([\"'])(.*)(\2)", line)
        if m:
            prefix, quote, value, _ = m.groups()
            if quote == '"' and '"' in value and "'" not in value:
                # Switch to single quotes outside
                return f"{prefix}'{value}'"
            elif quote == "'" and "'" in value and '"' not in value:
                # Switch to double quotes outside
                return f'{prefix}"{value}"'
            elif '"' in value and "'" in value:
                # Escape double quotes and use double quotes outside
                value = value.replace('"', r'\"')
                return f'{prefix}"{value}"'
        return line

    content = "\n".join(fix_quotes(line) for line in content.splitlines())

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Fixed: {file_path}")

def fix_all_locators(root_path):
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            if filename == "locators.py":
                fix_locators_file(os.path.join(dirpath, filename))

# Usage:
fix_all_locators(r"c:\Projects\PyBot\Object_Repository\PRA_Revera")