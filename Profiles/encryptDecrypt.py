import logging as logger
from math import log
import os
from cryptography.fernet import Fernet, InvalidToken
import base64, hashlib
import json
import re
import tkinter as tk
from tkinter import messagebox
import sys

class Security():

    @staticmethod
    def get_fernet_from_password(password: str):    
        key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
        fernet = Fernet(key)
        return fernet

    key = "Kunal"
    encrypt_keys = {"app_password", "dbpassword", "ssh_password", "sftp_password", "ccb_owner_password"}
    
    '''This function is used to create New, Update or Delete profile based on the provided path, body, and action type i.e. new, update, delete.'''
    @staticmethod
    def profile_action(path, body, action):
        project_root = os.getcwd()
        root_path= os.path.join(project_root, "Profiles")
        filePath= os.path.join(root_path, "mainProfile.py")
        action=action.lower()
        if action == "update":
            Security.update_and_encrypt_json(path, body)
            Security.reset_profile_variables(filePath)
        elif action == "new":
            Security.create_and_encrypt_json(path, body)
            Security.reset_profile_variables(filePath)
        elif action == "delete":
            Security.delete_file_with_confirmation(path)
            Security.reset_profile_variables(filePath)
        else:
            raise ValueError("Invalid action specified")
        print(f"Profile action: {action}")


    '''This function creates a new encrypted JSON file with the provided updates.'''
    @staticmethod
    def create_and_encrypt_json(path: str, updates: dict):
        if os.path.exists(path):
             root = tk.Tk()
             root.withdraw()
             messagebox.showinfo("Environment File Exists", "File already exists, please select action as 'UPDATE' instead of 'NEW'.")
             root.destroy()
             print("Environment File already exists, operation stopped.")
             return
        fernet = Security.get_fernet_from_password(Security.key)
        # Step 1: Filter out keys with None or empty values
        clean_data = {k: v for k, v in updates.items() if v not in [None, ""]}
        # Step 2: Encrypt only the specified keys
        keys_to_encrypt = Security.encrypt_keys
        processed_data = {}
        for k, v in clean_data.items():
            if k.lower() in keys_to_encrypt:
                processed_data[k] = fernet.encrypt(str(v).encode()).decode()
            else:
                processed_data[k] = v
        # Step 3: Ensure directory exists
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except Exception as e:
            print(f"Error creating directory: {e}")
            logger.error(f"Error creating directory: {e}")
            return
        # Step 4: Write to new JSON file
        with open(path, "w") as file:
            json.dump(processed_data, file, indent=4)
        print(f"New encrypted JSON created at: {path}")
    
    '''This function updates an existing encrypted JSON file with new values, encrypts them, and saves the file.
    It only updates values that are not None or empty strings.'''
    @staticmethod
    def update_and_encrypt_json(path: str, updates: dict):
        if not os.path.exists(path):
             root = tk.Tk()
             root.withdraw()
             messagebox.showinfo("Environment File Doesn't Exist", "File doesn't exist, please select action as 'NEW' instead of 'UPDATE'.")
             root.destroy()
             print("Environment File doesn't exist, operation stopped.")
             return
        fernet = Security.get_fernet_from_password(Security.key)
        keys_to_encrypt = Security.encrypt_keys
        # Step 1: Load existing JSON and decrypt only the specified keys
        with open(path, "r") as file:
            encrypted_data = json.load(file)
        data = {}
        for k, v in encrypted_data.items():
            if k.lower() in keys_to_encrypt:
                try:
                    data[k] = fernet.decrypt(v.encode()).decode()
                except Exception as e:
                    raise ValueError(f"Decryption failed for key '{k}'. Make sure file is encrypted and key is correct. Error: {e}")
            else:
                data[k] = v
        # Step 2: Update only the values that are not None or empty strings
        for k, v in updates.items():
            if v is not None and v != "" and v != "None":
                data[k] = v
        # Step 3: Encrypt only the specified keys, leave others as plain text
        encrypted_updated_data = {}
        for k, v in data.items():
            if k.lower() in keys_to_encrypt:
                encrypted_updated_data[k] = fernet.encrypt(str(v).encode()).decode()
            else:
                encrypted_updated_data[k] = v
        # Step 4: Save encrypted JSON back to the file
        with open(path, "w") as file:
            json.dump(encrypted_updated_data, file, indent=4)
        print(f"Updated and encrypted JSON saved to: {path}")
        
        
    '''This function decrypts an encrypted JSON file and saves the decrypted content back to the same file.
    It assumes the file is in encrypted JSON format.'''    
    @staticmethod
    def decrypt_json_file(path: str) -> dict:
        fernet = Security.get_fernet_from_password(Security.key)
        # Read encrypted file (must be in encrypted JSON format)
        with open(path, "r") as file:
            encrypted_data = json.load(file)
        # Only decrypt the specified keys, leave others as-is
        keys_to_decrypt = Security.encrypt_keys
        decrypted_data = {}
        for k, v in encrypted_data.items():
            if k.lower() in keys_to_decrypt:
                try:
                    decrypted_data[k] = fernet.decrypt(v.encode()).decode()
                except InvalidToken:
                    logger.info(f"Key '{k}' appears to be already decrypted.")
                    decrypted_data[k] = v
                except Exception as e:
                    raise ValueError(f"Decryption failed for key '{k}'. Make sure file is encrypted and key is correct. Error: {e}")
            else:
                decrypted_data[k] = v
        # Overwrite same file with decrypted JSON
        with open(path, "w") as file:
            json.dump(decrypted_data, file, indent=4)
        print(f"Decrypted and saved to same file: {path}")

    '''This function encrypts an existing JSON file by encrypting each value and saving it back to the same file.
    It assumes the file is in plain JSON format.'''    
    @staticmethod
    def encrypt_json_file(path: str):
        fernet = Security.get_fernet_from_password(Security.key)
        # Load existing JSON data
        with open(path, "r") as file:
            data = json.load(file)
        # Encrypt only the specified keys, leave others as-is
        keys_to_encrypt = Security.encrypt_keys
        encrypted_data = {}
        for k, v in data.items():
            if k.lower() in keys_to_encrypt:
                encrypted_data[k] = fernet.encrypt(str(v).encode()).decode()
            else:
                encrypted_data[k] = v
        # Save encrypted data back to the same file
        with open(path, "w") as file:
            json.dump(encrypted_data, file, indent=4)
        print(f"Encrypted JSON saved to: {path}")
        
        
    '''This function deletes a file with a confirmation dialog.
    # It checks if the file exists, shows a confirmation dialog, and deletes the file if confirmed.'''
    @staticmethod
    def delete_file_with_confirmation(path: str):
        if not os.path.exists(path):
            print(f"File does not exist: {path}")
            return
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()
        # Show confirmation dialog
        response = messagebox.askyesno("Confirm Delete", f"Do you really want to delete:\n{path}?")
        root.destroy()
        if response:
            try:
                os.remove(path)
                print(f"File deleted: {path}")
            except Exception as e:
                print(f"Error deleting file: {e}")
        else:
            print("Deletion cancelled.")
    
    
    '''This function resets specific profile variables in a given file to "None".'''
    import re
    @staticmethod
    def reset_profile_variables(file_path):
        variables_to_reset= [
                "browser","url","app_username","app_password","dbType","host","port","dbusername","dbpassword","dbName","SSH_SERVER_IP","SSH_USERNAME","SSH_PASSWORD","sftp_username","sftp_password","SFTP_Server","CCB_OWNER_User_Name","CCB_OWNER_Password"
                ]
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return
        # Read the file content
        with open(file_path, 'r') as file:
            lines = file.readlines()
        # Track changes
        changes_made = 0
        # Process each line
        for i, line in enumerate(lines):
            # Skip comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                continue
            # Check if this line contains a variable assignment
            for var in variables_to_reset:
                # Match exact variable name followed by equals sign
                pattern = rf"^{re.escape(var)}\s*="
                if re.match(pattern, line.strip()):
                    # Replace with variable set to "None"
                    lines[i] = f'{var} = "None"\n'
                    #print(f"Reset {var} to None")
                    changes_made += 1
                    break
        # Write the modified content back if changes were made
        if changes_made > 0:
            with open(file_path, 'w') as file:
                file.writelines(lines)
            #print(f"\nUpdated {changes_made} variables in {file_path}")
        else:
            print("No variables were modified")