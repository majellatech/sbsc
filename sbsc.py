#!/usr/bin/env python3

""" a small application to check if the start time if the  current time somewhat matches
    the next planned broadcast time.
    if this is not the case, usually there was a missed a broadcast or someone accidentally started one twice
"""

# TODO: handle cases where there were no planned broadcasts in the first place


import urllib.request
import urllib.error
import json
import PySimpleGUI as sg
import datetime as dt
import os
import sys
import time

# Load configuration variables
with open("config.json") as config_file:
    conf = json.load(config_file)

channel_id = conf.get("channel_id")
api_key = conf.get("api_key")
resizable_screen = conf.get("resizable_screen")
time_margin = conf.get("time_margin")

# wait until the system time is synced via NTP
while True:
    ntp_synchronisatie_voltooid = os.system('timedatectl | grep System\ clock\ synchronized | grep -q yes') == 0
    if ntp_synchronisatie_voltooid:
        break
    else:
        time.sleep(1)

# Wait until internet connection is active
while True:
    try:
        urllib.request.urlopen('http://google.com')
        break
    except urllib.error.URLError as e:
        print(e.reason)
        time.sleep(1)

os.chdir(sys.path[0])

# fetch a list of video ids of planned broadcasts
upcoming_broadcasts_list_url = 'https://youtube.googleapis.com/youtube/v3/search?part=id&channelId={}&eventType=upcoming&maxResults=1000&order=date&type=video&key={}'.format(channel_id, api_key)
upcoming_broadcasts_list     = json.load(urllib.request.urlopen(upcoming_broadcasts_list_url))
upcoming_broadcast_ids       = video_ids = ','.join(list(map(lambda x: x['id']['videoId'], upcoming_broadcasts_list['items'])))

# determine next planned broadcast
upcoming_broadcasts_url    = 'https://youtube.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={}&key={}'.format(upcoming_broadcast_ids, api_key)
upcoming_broadcasts        = json.load(urllib.request.urlopen(upcoming_broadcasts_url))

# for some reason the API returns results for eventType=upcoming which were already broadcast
# the next line filters out these results
upcoming_broadcasts        = [broadcast for broadcast in upcoming_broadcasts['items'] if 'actualStartTime' not in broadcast['liveStreamingDetails']]
upcoming_broadcasts_sorted = sorted(upcoming_broadcasts, key=lambda k: k['liveStreamingDetails']['scheduledStartTime'])
first_upcoming_broadcast   = upcoming_broadcasts_sorted[0]

# get info on next planned broadcast
first_upcoming_broadcast_details_url = 'https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}'.format(first_upcoming_broadcast['id'], api_key)
first_upcoming_broadcast_details     = json.load(urllib.request.urlopen(first_upcoming_broadcast_details_url))
first_upcoming_broadcast_name        = first_upcoming_broadcast_details['items'][0]['snippet']['title']
first_upcoming_broadcast_start_time  = dt.datetime.strptime(first_upcoming_broadcast['liveStreamingDetails']['scheduledStartTime'], '%Y-%m-%dT%H:%M:%S%z')

# check if start time of next broadcast is within the default margin of 45 minutes ago
now = dt.datetime.now(tz=dt.timezone.utc)
margin = dt.timedelta(minutes=time_margin)
start_time_ok = now - margin <= first_upcoming_broadcast_start_time <= now + margin

# define the window
bg_color = 'green' if start_time_ok else 'red'
layout = [
    [sg.Text(key='expand_top', background_color=bg_color)],
    [sg.Image('images/checkmark.png' if start_time_ok else 'images/warning.gif', background_color=bg_color, key='image')],
    [sg.Text('Eerstvolgende geplande uitzending: {}'.format(first_upcoming_broadcast_name), background_color=bg_color, key='text1', font=('normal', 25), auto_size_text=True)],
    [sg.Text('Geplande uitzendtijd: {}'.format(first_upcoming_broadcast_start_time.astimezone().strftime('%c')), background_color=bg_color, key='text2', font=('normal', 25))],
    [sg.Text('Huidig tijdstip: {}'.format(dt.datetime.now().strftime('%X')), background_color=bg_color, font=('any', '25'))],
    [sg.Button('Sluiten')],
    [sg.Text(key='expand_bottom', background_color=bg_color)]
]
sg.set_options(background_color=bg_color)
window = sg.Window('Window', layout, finalize=True, resizable=resizable_screen,
                   text_justification='center', element_justification='center')

# ugly hack to center the text (see https://github.com/PySimpleGUI/PySimpleGUI/issues/3630)
window['expand_top'].expand(True, True, True)
window['expand_bottom'].expand(True, True, True)

# maximize the window
window.maximize()

# show window
while True:
    event, values = window.read(timeout=500)
    if not start_time_ok:
        window['image'].update_animation('images/warning.gif')
    if event == 'Sluiten':
        break
window.close()
