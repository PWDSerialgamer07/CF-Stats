import requests
from dotenv import load_dotenv
import os
import json
import sqlite3
'''
Putting this here so I don't forget:
most mainstream mods are on multiple versions and modloaders. For this, we'll look through its files and get the downloads for each versions and loader, then
we'll make duplicate entries in the db (one for each version and modloader supported) and add the downloads for each of them
'''

load_dotenv()
API_URL = "https://api.curseforge.com/"
API_KEY = os.getenv('key')

headers: dict = {
    'Accept': 'application/json',
    'x-api-key': API_KEY
}


def get_version_list() -> list:
    versions_raw = requests.get(
        API_URL + "v1/minecraft/version", headers=headers)
    versions_raw = versions_raw.json()
    # List of versions strings (because for some reason the api uses version strings instead of ids)
    versions: list = [item['versionString'] for item in versions_raw['data']]
    return versions


def get_mod_loaders_list() -> list:
    mod_loaders_raw = requests.get(
        API_URL + "v1/mods/loaders", headers=headers)
    mod_loaders_raw = mod_loaders_raw.json()
    # Now it uses ids instead of strings whyyyyy, it even returns the name as a string(which will be useful for displaying it to the user)
    mod_loaders: list = [item['type'] for item in mod_loaders_raw['data']]
    return mod_loaders


def main():
    versions = get_version_list()
    mod_loaders = get_mod_loaders_list()
