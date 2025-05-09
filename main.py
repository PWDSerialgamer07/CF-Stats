import requests
from dotenv import load_dotenv
import os
import json
import sqlite3
'''
Putting this here so I don't forget:
Instead it'll be one databse with one table containing each mods and their downloads for each version (and a total column), then another table which is just 
a mod loader per line with a single columns containing their downloads
Let's also have a temporary table to store mod urls before we parse throug each of them, or instead a different database with tables for each loaders? I'm not sure

Curseforge's fuck ass api only offers per mod statistics so I'm going to have to make a lot of request
Let's hope I don't instantly get rate limited or have my api key revoked
'''

# API setup
load_dotenv()
API_URL = "https://api.curseforge.com/"
API_KEY = os.getenv('key')

headers: dict = {
    'Accept': 'application/json',
    'x-api-key': API_KEY
}


# To escape column names since for sqlite3 you can't have column names be stuff like 1.21.2
def escape_column_name(name: str) -> str:
    return f'"{name}"'


# Self explanatory, just creating the db (if it doesn't exist)
def create_db(db_path: str = 'mods.sqlite3', version_list: list = []):
    # DB Setup
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Escaping Column Names
    data_type: str = "INTEGER"
    columns: list = []
    for i in version_list:
        column = f'{escape_column_name(i)} {data_type}'
        columns.append(column)
    # No need to put this one through escape_column_name I think
    columns.append('Total INTEGER')

    # Create DB Tables
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS Mods (
        mod_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        {', '.join(columns)}
    );
    CREATE TABLE IF NOT EXISTS Mod_Loaders (
        name TEXT PRIMARY KEY,
        downloads INTEGER
    );
    CREATE TABLE IF NOT EXISTS Mod_Urls (
        mod_id INTEGER,
        name TEXT
    )
    ''')  # Should create a column for each versions available in the mod table, also we're not getting per version downloads for the mod loaders
    conn.commit()
    return conn


def insert_mod(conn, mod_data: dict, version_list: list):
    """
    mod_data should be a a dictionary, something like this (all mods passed with mod_data should have at least 1K downloads):
    {
        'mod_id': 0,
        'name': 'example_mod',
        '1.21.2': 1234,
        '1.20.1': 4590
        'total': 5824 # Optional, maybe we calculate it here? or not the API sends the total I think
    }
    mod loaders will be handled in another function.

    mod list is passed to compare the versions in mod_data with it, so that if the mod doesn't have a version in version_list, we add it in the dictionnary with 0 downloads
    """
    cur = conn.cursor()
    mod_id = mod_data['mod_id']
    name = mod_data['name']
    for i in version_list:
        if i not in mod_data:
            # If the mod doesn't have a version in version_list, we add it in the dictionary with 0 downloads
            mod_data[i] = 0
    # Now, how will I add those values to the database? I have no idea so TODO: Find a way to add them to the database

    conn.commit()


def insert_temp_mod(conn, mod_name: str, mod_id: int):
    cur = conn.cursor()
    cur.execute('''
    INSERT INTO Mod_Urls (id, name) VALUES (?, ?)
    ''', (mod_id, mod_name))
    conn.commit()


# Pretty simple, actually getting the mod_loader_data will be the hard part
def insert_mod_loader(conn, mod_loader_data: dict):
    cur = conn.cursor()
    name = mod_loader_data['name']
    downloads = mod_loader_data['downloads']
    cur.execute('''
    INSERT OR IGNORE INTO Mod_Loaders (name, downloads) VALUES (?, ?)
    ''', (name, downloads))
    conn.commit()


# Self explanatory, just getting the list of versions
def get_version_list() -> list:
    versions_raw = requests.get(
        API_URL + "v1/minecraft/version", headers=headers)
    versions_raw = versions_raw.json()
    # List of versions strings (because for some reason the api uses version strings instead of ids)
    versions: list = [item['versionString'] for item in versions_raw['data']]
    return versions


# Same as above except we're getting the list of mod loaders
def get_mod_loaders_list() -> list:
    mod_loaders_raw = requests.get(
        API_URL + "v1/mods/loaders", headers=headers)
    mod_loaders_raw = mod_loaders_raw.json()
    # Now it uses ids instead of strings whyyyyy, it even returns the name as a strings so why offer both
    # I kinda dislike these one liners so I might change it later
    mod_loaders: list = [item['type'] for item in mod_loaders_raw['data']]
    return mod_loaders


def main():
    versions = get_version_list()
    mod_loaders = get_mod_loaders_list()
    con = create_db(version_list=versions)
    for version in versions:
        for mod_loader in mod_loaders:
            index = 0
            while True:
                # Here's to many more api requests
                mods_raw = requests.get(API_URL + f"v1/mods/search", params={
                    'gameVersion': version,
                    'modLoaderType': mod_loader,
                    'index': index
                }, headers=headers)
                mods_raw = mods_raw.json()
                index += 50
                for item in mods_raw['data']:
                    if item['downloadCount'] <= 1000:
                        continue
                    id = item['id']
                    name = item['name']
                    insert_temp_mod(con, name, id)

                if mods_raw["pagination"]["resultCount"] == 0:
                    break
