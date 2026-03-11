import json
import os

FILE_DB="files.json"
CODE_DB="codes.json"
USER_DB="users.json"

def load(file):
    if not os.path.exists(file):
        return {}
    with open(file) as f:
        return json.load(f)

def save(file,data):
    with open(file,"w") as f:
        json.dump(data,f)

files=load(FILE_DB)
codes=load(CODE_DB)
users=load(USER_DB)

def save_all():
    save(FILE_DB,files)
    save(CODE_DB,codes)
    save(USER_DB,users)
