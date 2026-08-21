from csv import excel
from itertools import count
from math import log
import re
import logging as logs
import ast
import xml.etree.ElementTree as ET


def parse_default_value(name, default):
    val = default.strip()
    # Boolean
    if val.lower() == 'true':
        return True
    elif val.lower() == 'false':
        return False
    # Integer
    elif re.fullmatch(r'-?\d+', val):
        return int(val)
    # Float
    elif re.fullmatch(r'-?\d+\.\d+', val):
        return float(val)
    # List
    elif val.startswith('[') and val.endswith(']') and not val.startswith('[('):
        try:
            return ast.literal_eval(val)
        except Exception:
            return val
    # Map/Dict (Groovy style: [('key') : value, ...])
    elif val.startswith("[("):
        # Fix: Replace [ and ] with {}, remove extra quotes around keys
        corrected = val.replace("[", "{").replace("]", "}").replace("(","").replace(")", "")
        parsed = ast.literal_eval(corrected)
        return parsed
    # Map/Dict (Python style)
    elif val.startswith('{') and val.endswith('}'):
        try:
            return ast.literal_eval(val)
        except Exception:
            return val
    # String (single or double quoted)
    elif (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
        unquoted = val[1:-1]
        return unquoted
    # GlobalVariable or other code (not quoted)
    elif val.startswith('GlobalVariable.'):
        return val  # treat as string, not variable
    elif re.match(r'^[A-Za-z_][A-Za-z0-9_\.]*$', val):
        return val  # treat as variable/expression
    # Fallback: treat as string
    else:
        return val

def extract_variables_from_tc(tc_file_path):
    variables = []
    tree = ET.parse(tc_file_path)
    root = tree.getroot()
    for var in root.findall('.//variable'):
        name = var.find('name')
        default = var.find('defaultValue')
        if name is not None and default is not None:
            variables.append((name.text.strip(), default.text.strip()))
    return variables

def insert_variables_into_py(py_file_path, variables):
    with open(py_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    new_lines = []
    inserted = False
    def_pattern = re.compile(r'^\s*def\s+test_\w*\s*\(.*\)\s*:')
    for idx, line in enumerate(lines):
        new_lines.append(line)
        if not inserted and def_pattern.match(line):
            # Find the indentation level
            indent = re.match(r'^(\s*)', line).group(1) + '    '
            # Insert variable assignments after the function definition line
            for name, default in variables:
                #print(f"Processing variable: {name} with default: {default}")
                value = parse_default_value(name, default)
                #print(f"Inserting variable: {name} : {value}")
                # Format value for Python code
                if isinstance(value, dict):
                    # Format dict in multiple lines with proper indentation
                    countV= 1
                    dict_str = "{\n"
                    for k, v in value.items():
                        if countV != len(value.items()):
                            if isinstance(v, str):
                                dict_str += f"{indent}    '{k}': '{v}',\n"
                            else:
                                dict_str += f"{indent}    '{k}': {v},\n"                        
                        else:
                            if isinstance(v, str):
                                dict_str += f"{indent}    '{k}': '{v}'\n"
                            else:
                                dict_str += f"{indent}    '{k}': {v}\n"
                        countV += 1
                    dict_str += f"{indent}}}"
                    new_lines.append(f"{indent}{name} = {dict_str}\n")
                elif isinstance(value, str):
                    # If value starts with GlobalVariable., always quote as string
                    if value.startswith('GlobalVariable.'):
                        new_lines.append(f"{indent}{name} = '{value}'\n")
                    else:
                        new_lines.append(f"{indent}{name} = {repr(value)}\n")
                else:
                    new_lines.append(f"{indent}{name} = {repr(value)}\n")
            inserted = True
    with open(py_file_path, 'w', encoding='utf-8') as f:
        f.write(f'#Variables migrated from .tc file\n')
        f.writelines(new_lines)

def readPathFromExcel(excel_path):
    import pandas as pd
    df = pd.read_excel(excel_path)  
    print("Unique Status values:", df['Status'].unique())
    df['Status'] = df['Status'].astype(str).str.strip().str.lower()
    df_filtered = df[df['Status'] == 'open']
    if df_filtered.empty:
        raise ValueError("No open test cases found in the Excel file for variable Migration.")
    if 'Katalon TC file path' in df_filtered.columns:
        katalonPath =  df_filtered['Katalon TC file path'].tolist()
    else:
        raise ValueError("Excel file must contain a 'Katalon TC file path' column.")
    if 'Playwright Testcase path' in df_filtered.columns:
        Pybot_PYpaths =  df_filtered['Playwright Testcase path'].tolist()
    else:
        raise ValueError("Excel file must contain a 'Playwright Testcase path' column.")
    for tc_path, py_path in zip(katalonPath, Pybot_PYpaths):
        print(f"Processing Katalon TC: {tc_path} -> Playwright PY: {py_path}")
        variables = extract_variables_from_tc(tc_path)
        insert_variables_into_py(py_path, variables)
        print(f"Inserted {len(variables)} variables into {py_path}")
        comment = f"Inserted {len(variables)} variables into {py_path}"
        if len(variables) == 0:
            comment = f"No variables found to migrate."
        # Update the status in the original dataframe, not just the filtered view
        df.loc[df['Katalon TC file path'] == tc_path, 'Status'] = 'Migrated'
        df.loc[df['Katalon TC file path'] == tc_path, 'Comments'] = comment
    df.to_excel(excel_path, sheet_name='Sheet1', index=False)

if __name__ == "__main__":
    # Set your file paths here
    '''
    tc_file_path = r'C:\Kunal_gitRepo\revera-qa-repo\Test Cases\20.4_Version\Product Engineering\PRAC-243865_Mask Unmask PII\Capture Ticket\1. Mask_Unmask PII Button validation.tc'  # Change as needed
    py_file_path = r'C:\Py_project\revera-qa-repo\Test_Cases\PRA_Testcases\test_CaptureTicketMask.py'  # Change as needed
    variables = extract_variables_from_tc(tc_file_path)
    insert_variables_into_py(py_file_path, variables)
    print(f"Inserted {len(variables)} variables into {py_file_path}")  
    '''
    import os
    project_root = os.getcwd()
    # Read paths from Excel file
    excel_path = os.path.join(project_root, "Test_Cases\Variable_Migration", "MigratedTC.xlsx")
    #excel_path = r'C:\Users\Rupal.mehta\PyBot_Project\revera-qa-repo\Test_Cases\MigratedTC.xlsx'
    readPathFromExcel(excel_path)

