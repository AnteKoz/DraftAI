import json
import sqlite3
import time
from sqlite3 import Error

import requests


def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(r"enemies.db")
        return conn
    except Error as e:
        print(e)

    return conn


def get_header(dev_key):
    headers = {
        "X-Riot-Token": dev_key
    }
    return headers


def get_puuids(dev_key, names):
    puuids = []
    for name in names:
        player_url = "https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + str(name)
        player_response = requests.request("GET", url=player_url, headers=get_header(dev_key))
        puuid = json.loads(player_response.text).get("puuid")
        puuids.append(puuid)
    return puuids


def get_match_ids_from_flex(dev_key, puuid):

    all_match_ids = []
    for i in range(0, 5):
        matches_url = "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/" + puuid + "/ids?queue=440&start="+str(i*100)+"&count=100"
        matches_response = requests.request("GET", url=matches_url, headers=get_header(dev_key))
        match_ids = json.loads(matches_response.text)
        all_match_ids.extend(match_ids)
        if len(match_ids) < 100:
            return all_match_ids

    return all_match_ids


if __name__ == '__main__':

    dev_key = "RGAPI-3a86957c-27d3-4059-9279-cc72e07363d3"

    names = ["kevler287"]
    puuids = get_puuids(dev_key, names)
    print("puuids: "+str(puuids))

    match_ids = set()
    for puuid in puuids:
        match_ids.update(get_match_ids_from_flex(dev_key, puuid))
    print(str(match_ids))
