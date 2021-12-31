#!/usr/bin/env python3

# Een klein programmaatje om te controleren of de starttijd van de eerstvolgende geplande
# YouTubeuitzending ongeveer overeenkomt met het huidige tijdstip.
# Als dit niet zo is, is er meestal per ongeluk een uitzending overgeslagen of is er per ongeluk
# twéé keer achter elkaar een uitzending gestart.

# Nog te doen: afhandelen van gevallen waarin er überhaupt geen geplande uitzendingen zijn.

import urllib.request
import urllib.error
import json
import PySimpleGUI as sg
import datetime as dt
import os
import time

channel_id = ''
api_key = ''

# Wacht tot systeemklok via NTP is gesynchroniseerd
while True:
    ntp_synchronisatie_voltooid = os.system('timedatectl | grep System\ clock\ synchronized | grep -q yes') == 0
    if ntp_synchronisatie_voltooid:
        break
    else:
        time.sleep(1)

# Wacht totdat er een verbinding met het internet is
while True:
    try:
        urllib.request.urlopen('http://google.com')
        break
    except urllib.error.URLError as e:
        print(e.reason)
        time.sleep(1)

# Wijzig werkmap
os.chdir('/home/pi/sbsc/')

# Haal lijst met video ids van geplande uitzendingen op
upcoming_broadcasts_list_url = 'https://youtube.googleapis.com/youtube/v3/search?part=id&channelId={}&eventType=upcoming&maxResults=1000&order=date&type=video&key={}'.format(channel_id, api_key)
upcoming_broadcasts_list     = json.load(urllib.request.urlopen(upcoming_broadcasts_list_url))
upcoming_broadcast_ids       = video_ids = ','.join(list(map(lambda x: x['id']['videoId'], upcoming_broadcasts_list['items'])))

# Bepaal eerstvolgende geplande uitzending
upcoming_broadcasts_url    = 'https://youtube.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={}&key={}'.format(upcoming_broadcast_ids, api_key)
upcoming_broadcasts        = json.load(urllib.request.urlopen(upcoming_broadcasts_url))
# Om een mij onduidelijke reden geeft de API soms resultaten terug voor "eventType=upcoming" die
# reeds uitgezonden zijn. Onderstaande regel filtert deze resultaten eruit.
upcoming_broadcasts        = [broadcast for broadcast in upcoming_broadcasts['items'] if not 'actualStartTime' in broadcast['liveStreamingDetails']]
upcoming_broadcasts_sorted = sorted(upcoming_broadcasts, key = lambda k : k['liveStreamingDetails']['scheduledStartTime'])
first_upcoming_broadcast   = upcoming_broadcasts_sorted[0]

# Haal info eerstvolgende geplande uitzending op
first_upcoming_broadcast_details_url = 'https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}'.format(first_upcoming_broadcast['id'], api_key)
first_upcoming_broadcast_details     = json.load(urllib.request.urlopen(first_upcoming_broadcast_details_url))
first_upcoming_broadcast_name        = first_upcoming_broadcast_details['items'][0]['snippet']['title']
first_upcoming_broadcast_start_time  = dt.datetime.strptime(first_upcoming_broadcast['liveStreamingDetails']['scheduledStartTime'], '%Y-%m-%dT%H:%M:%S%z')

# Controleer of starttijd van eerstvolgende geplande uitzending binnen 45 minuten van de huidige
# tijd valt
now = dt.datetime.now(tz=dt.timezone.utc)
margin = dt.timedelta(minutes = 45)
start_time_ok = now - margin <= first_upcoming_broadcast_start_time <= now + margin

# Definieer venster
bg_color = 'green' if start_time_ok else 'red'
layout = [
    [sg.Text(key='expand_top', background_color = bg_color)],
    [sg.Image('checkmark.png' if start_time_ok else 'warning.gif', background_color = bg_color, key = 'image')],
    [sg.Text('Eerstvolgende geplande uitzending: {}'.format(first_upcoming_broadcast_name), background_color = bg_color, key = 'text1', font = ('normal', 25), auto_size_text = True)],
    [sg.Text('Geplande uitzendtijd: {}'.format(first_upcoming_broadcast_start_time.astimezone().strftime('%c')), background_color = bg_color, key = 'text2', font = ('normal', 25))],
    [sg.Text('Huidig tijdstip: {}'.format(dt.datetime.now().strftime('%X')), background_color = bg_color, font = ('any', '25'))],
    [sg.Button('Sluiten')],
    [sg.Text(key='expand_bottom', background_color = bg_color)]
]
sg.set_options(background_color = bg_color)
window = sg.Window('Window', layout, finalize = True, resizable = True,
                   text_justification = 'center', element_justification = 'center')

# Lelijke hack om verticaal te centreren (https://github.com/PySimpleGUI/PySimpleGUI/issues/3630)
window['expand_top'].expand(True, True, True)
window['expand_bottom'].expand(True, True, True)

# Maak schermvullend
window.maximize()

# Toon venster
while True:
    event, values = window.read(timeout=500)
    if not start_time_ok:
        window['image'].update_animation('warning.gif')
    if event == 'Sluiten':
        break
window.close()
