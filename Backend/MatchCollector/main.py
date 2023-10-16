import json
import sqlite3
import time
from sqlite3 import Error

import requests


def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(r"matches.db")
        return conn
    except Error as e:
        print(e)

    return conn


def get_header(dev_key):
    headers = {
        "X-Riot-Token": dev_key
    }
    return headers


def get_puuid(dev_key, name):
    player_url = "https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + str(name)
    player_response = requests.request("GET", url=player_url, headers=get_header(dev_key))
    puuid = json.loads(player_response.text).get("puuid")
    print("Player ID: " + puuid)
    return puuid


def get_match_ids(dev_key, puuid):
    matches_url = "https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/" + puuid + "/ids?queue=420&start=0&count=90"
    matches_response = requests.request("GET", url=matches_url, headers=get_header(dev_key))
    match_ids = json.loads(matches_response.text)
    print("Match ID's: " + str(match_ids))
    return match_ids


def process_match(dev_key, match_id, conn):
    cursor = conn.cursor()
    count = cursor.execute("Select count (*) from all_matches where match_id = ?", [match_id]).fetchone()[0]
    if count > 0:
        print("Match already in database")
        return None

    match_url = "https://europe.api.riotgames.com/lol/match/v5/matches/" + str(match_id)
    match_response = requests.request("GET", url=match_url, headers=get_header(dev_key))
    game_info = json.loads(match_response.text).get("info")
    if game_info is None:
        return None

    if game_info.get("gameMode") != "CLASSIC":
        print("Match is not classic")
        return None

    version_numbers = game_info.get("gameVersion").split(".")
    patch = str(version_numbers[0]) + "." + str(version_numbers[1])

    participants = game_info.get("participants", [])
    t1_top = t1_jgl = t1_mid = t1_adc = t1_sup = t2_top = t2_jgl = t2_mid = t2_adc = t2_sup = None
    for participant in participants:
        t1_top, t2_top = fill_variable(participant, "TOP", t1_top, t2_top)
        t1_jgl, t2_jgl = fill_variable(participant, "JUNGLE", t1_jgl, t2_jgl)
        t1_mid, t2_mid = fill_variable(participant, "MIDDLE", t1_mid, t2_mid)
        t1_adc, t2_adc = fill_variable(participant, "BOTTOM", t1_adc, t2_adc)
        t1_sup, t2_sup = fill_variable(participant, "UTILITY", t1_sup, t2_sup)

    win = None
    teams = json.loads(match_response.text).get("info").get("teams", [])
    if teams[0].get("win"):
        win = str(teams[0].get("teamId"))
    else:
        win = str(teams[1].get("teamId"))

    if None in [match_id, patch, t1_top, t1_jgl, t1_mid, t1_adc, t1_sup, t2_top, t2_jgl, t2_mid, t2_adc, t2_sup, win]:
        return json.loads(match_response.text).get("metadata").get("participants")

    instance = [match_id, patch, t1_top, t1_jgl, t1_mid, t1_adc, t1_sup, t2_top, t2_jgl, t2_mid, t2_adc, t2_sup, win]
    print(instance)

    cursor.execute(
        "Insert into all_matches (match_id, patch, t1_top, t1_jng, t1_mid, t1_adc, t1_sup, t2_top, t2_jgl, t2_mid, t2_adc, t2_sup, win) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [match_id, patch, t1_top, t1_jgl, t1_mid, t1_adc, t1_sup, t2_top, t2_jgl, t2_mid, t2_adc, t2_sup, win])
    conn.commit()

    return json.loads(match_response.text).get("metadata").get("participants")


def fill_variable(participant, teamPosition, t1_var, t2_var):
    if participant.get("teamPosition") == teamPosition:
        if participant.get("teamId") == 100:
            t1_var = participant.get("championId")
        else:
            t2_var = participant.get("championId")

    return t1_var, t2_var


if __name__ == '__main__':

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS all_matches (match_id text primary key, patch text, t1_top integer, t1_jng integer, t1_mid integer, t1_adc integer, t1_sup integer, t2_top integer, t2_jgl integer, t2_mid integer, t2_adc integer, t2_sup integer, win text);")

    dev_key = "RGAPI-7b5e38b1-17da-4508-9981-7064a6c9e150"
    start_name = "Weldope"
    start_puuid = get_puuid(dev_key, start_name)
    time_spent = 0

    used_puuids = [start_puuid]
    master_match_ids = get_match_ids(dev_key, start_puuid)

    counter = 0
    while time_spent < 30000:

        if counter == len(master_match_ids):
            break

        puuids = process_match(dev_key, master_match_ids[counter], conn)
        counter = counter + 1
        if puuids is None:
            continue

        for puuid in puuids:
            if puuid in used_puuids:
                continue
            match_ids = get_match_ids(dev_key, puuid)
            for match_id in match_ids:
                process_match(dev_key, match_id, conn)

            used_puuids.append(puuid)

            print("Games fetched, wait 2 min now")
            time.sleep(121)
            time_spent = time_spent + 125
            print("Time spent: " + str(time_spent))
