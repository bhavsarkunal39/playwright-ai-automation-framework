# Product and Profile details
product = "PROJECT"
profile="DEFAULT"    
# action = "new" , "update", "delete"
action = "new"


#--------Profile details---------------------------------------
browser = "None"
url = "None"
app_username = "None"
app_password = "None"
dbType = "None"
host = "None"
port = "None"
dbusername = "None"
dbpassword = "None"
dbName = "None"
SSH_SERVER_IP = "None"
SSH_USERNAME = "None"
SSH_PASSWORD = "None"
sftp_username = "None"
sftp_password = "None"
SFTP_Server = "None"
SWO_Enabled = "None"
PostURL = "None"
CCB_OWNER_User_Name = "None"
CCB_OWNER_Password = "None"
#-----------------------------------------------------------------






#-----------------------------------------------------------------
#---------------------Internal logic------------------------------
import os
import json
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import Keywords.projectVariables as globalVar
productName= product.upper()  # Convert product name to uppercase
profileName = profile.upper()  # Convert profile name to uppercase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
profilePath = os.path.join(globalVar.profilePath, f"{profileName}.json")
print(f"Profile path: {profilePath}")
print(f"Profile folder: {globalVar.profilePath}")
body = {
    "browser": browser,
    "url": url,
    "app_username": app_username,
    "app_password": app_password,
    "dbType": dbType,
    "host": host,
    "port": port,
    "dbusername": dbusername,
    "dbpassword": dbpassword,
    "dbName": dbName,
    "SSH_SERVER_IP": SSH_SERVER_IP,
    "SSH_USERNAME": SSH_USERNAME,
    "SSH_PASSWORD": SSH_PASSWORD,
    "sftp_username": sftp_username,
    "sftp_password": sftp_password,
    "SFTP_Server": SFTP_Server,
    "SWO_Enabled": SWO_Enabled,
    "PostURL": PostURL,
    "CCB_OWNER_User_Name": CCB_OWNER_User_Name,
    "CCB_OWNER_Password": CCB_OWNER_Password
}

import json # Ensure the Profiles module is correctly imported
import sys
project_root = os.getcwd()
root_path= os.path.join(project_root, "Profiles")
filePath= os.path.join(root_path, "mainProfile.py")
sys.path.append(project_root)
from Profiles.encryptDecrypt import Security
if __name__ == "__main__":
    Security.profile_action(profilePath, body, action)
    if len(sys.argv) > 1:
        vars_to_reset = sys.argv[1:]

