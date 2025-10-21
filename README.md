# pi-firebase-updater

## Virtual Environment
This project makes usage of Virtual Environment

1. to create a new virtual env
python3 -m venv venv

2. to activate the environment
source venv/bin/activate

3. to reset the environment
deactivate (if active)
rm -rf venv
... then create it again

## Install requirements.txt

pip install -r requirements.txt

## Issues
If you encounter something like

Traceback (most recent call last):
  File "/Users/matteopelucco/dev/git/github/matteopelucco/pi-firebase-updater/firebase-updater-rest.py", line 7, in <module>
    from google.oauth2 import service_account
ModuleNotFoundError: No module named 'google.oauth2'

Try the following: 

pip install --upgrade google-auth