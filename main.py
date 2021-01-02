from unity.initial_unpack import unpack_all_assets
from unity.unpack import unpack_new_assets
from api.discord import deliver
import api.servers as server
import config

from zipfile import ZipFile
import asyncio
import os as fs
import requests
import time
import pytz
import datetime
import json
import re
import crc16
from googletrans import Translator
from colorama import init, Fore, Style
import shutil
init(autoreset=True)

print('\n __    ____               .__  _______          \n|  | _/_   | _____ ______ |  | \   _  \   ______\n|   / /|   |/     \\\____ \|  | /  /_\  \ /  ___/\n|    < |   |  Y Y  \  |_> >  |_\  \_/   \\\___ \ \n|__|_ \|___|__|_|  /   __/|____/\_____  /____  >\n     \/          \/|__|               \/     \/ \nthis software was wrote by k1mpl0s.\n')

loop = asyncio.get_event_loop()

if not fs.path.isdir('./data'):
    fs.mkdir('./data')
    if not fs.path.isdir('./data/gb'):
        fs.mkdir('./data/gb')
    if not fs.path.isdir('./data/jp'):
        fs.mkdir('./data/jp')
    if not fs.path.isdir('./data/kr'):
        fs.mkdir('./data/kr')
    if not fs.path.isdir('./data/gb/overview'):
        fs.mkdir('./data/gb/overview')
    if not fs.path.isdir('./data/jp/overview'):
        fs.mkdir('./data/jp/overview')
    if not fs.path.isdir('./data/kr/overview'):
        fs.mkdir('./data/kr/overview')
    print(Fore.LIGHTYELLOW_EX + '[!] "data" directory created.')
if not fs.path.isdir('./resources'):
    fs.mkdir('./resources')
    if not fs.path.isfile('./resources/gb_config.json'):
        f = open('./resources/gb_config.json', 'w')
        f.write(
            '{"maint_timestamp": "", "maint_content_crc": "", "previous_sub": "", "relative_sub": "", "previous_version": [], "version": ""}')
        f.close()
    if not fs.path.isfile('./resources/jp_config.json'):
        f = open('./resources/jp_config.json', 'w')
        f.write(
            '{"maint_timestamp": "", "maint_content_crc": "", "previous_sub": "", "relative_sub": "", "previous_version": [], "version": ""}')
        f.close()
    if not fs.path.isfile('./resources/kr_config.json'):
        f = open('./resources/kr_config.json', 'w')
        f.write(
            '{"maint_timestamp": "", "maint_content_crc": "", "previous_sub": "", "relative_sub": "", "previous_version": [], "version": ""}')
        f.close()
    if not fs.path.isfile('./resources/notices.json'):
        f = open('./resources/notices.json', 'w')
        f.write('{"gb": [], "jp": [], "kr": []}')
        f.close()
    if not fs.path.isfile('./resources/notices.json'):
        f = open('./resources/single_notices.json', 'w')
        f.write('{"gb": [], "jp": [], "kr": []}')
        f.close()
    if not fs.path.isfile('./resources/skip.json'):
        f = open('./resources/skip.json', 'w')
        f.write('{"regular": [], "irregular": [], "pickup": [], "stepup": []}')
        f.close()
    print(Fore.LIGHTYELLOW_EX + '[!] "resources" directory created.')


# clean unnecessary text from patch notes.
def clean_note(ver, note):
    if ver == 'gb':
        note = note.replace('★New Contents Update★', '<:gem:585340092634234880>    **New content:**')
        note = note.replace('★New Hero★', '<:gem:585340092634234880>    **New character:**')
        note = note.replace('<span style=""font-size:35px"">', '')
        note = note.replace('<span style=""color:#131665"">', '')
        note = note.replace('We are currently undergoing maintenance <br>in order to bring you a better experience.', '')
        note = note.replace(
            '<br>You can also view a more detailed <br>update notice in the Official Community!<br><br>We sincerely thank everyone for enjoying 7DS.',
            '')
        note = note.replace('<br><br>', '\n\n')
        note = note.replace('<br>', '\n')
        return note
    elif ver == 'jp':
        note = note.replace('■', '<:gem:585340092634234880>')
        note = note.replace('<br><br>', '\n\n')
        note = note.replace('<br>', '\n')
        if config.translate_maint:
            translator = Translator()
            note = translator.translate(note).text
        return note
    elif ver == 'kr':
        note = note.replace('■', '<:gem:585340092634234880>    ')
        note = note.replace('<br><br>', '\n\n')
        note = note.replace('<br>', '\n')
        if config.translate_maint:
            translator = Translator()
            note = translator.translate(note).text
        return note


# start polling data from servers.
def begin_poll(ver):
    urls, folders = None, None
    if ver == 'gb':
        urls = config.gb_urls
        folders = config.gb_folders
    elif ver == 'jp':
        urls = config.jp_urls
        folders = config.jp_folders
    elif ver == 'kr':
        urls = config.kr_urls
        folders = config.kr_folders
    configuration = json.loads(open(f"./resources/{ver}_config.json", 'r').read())
    # check for new maintenance patch-note
    if config.check_maint:
        print(Fore.LIGHTYELLOW_EX + f"[{str(ver).upper()}] checking maintenance...")
        maint = server.get_maintenance(ver, int(round(time.time() * 1000)))
        if maint is not None and 'apiData' in maint:
            if 'endDateTime' in maint['apiData']:
                d = datetime.datetime.strptime(str(maint['apiData']['endDateTime']), '%Y-%m-%d %H:%M:%S')
                tz = pytz.timezone('Asia/Tokyo')
                d = tz.localize(d)
                jst = d.strftime('%I:%M %p').lower().replace(' ', '')
                est = pytz.timezone('America/New_York')
                pst = pytz.timezone('America/Los_Angeles')
                end_time = '\n\n<:gem:585340092634234880>    **Maint end:**\n' + d.strftime(
                    '%m/%d/%Y') + '\nJST - ' + jst + '\nEST - ' + d.astimezone(est).strftime(
                    '%I:%M %p').lower().replace(
                    ' ', '') + '\nPDT - ' + d.astimezone(pst).strftime("%I:%M %p").lower().replace(' ', '')
                # print(Fore.LIGHTCYAN_EX + '   -> ' + str(maint['apiData']['endDateTime']))
                # cdate = datetime.datetime.now().timestamp()
                last_timestamp = configuration['maint_timestamp']
                if int(d.timestamp()) != int(last_timestamp) and int(d.timestamp()) > int(last_timestamp):
                    configuration['maint_timestamp'] = str(int(d.timestamp()))
                    f = open(f"./resources/{ver}_config.json", 'w')
                    f.write(json.dumps(configuration))
                    f.close()
            else:
                end_time = '\n\n<:gem:585340092634234880>    **Maint end: **'
            if 'contents' in maint['apiData']:
                crc = crc16.crc16xmodem(bytes(maint['apiData']['contents'], 'utf-8'))
                crc2 = configuration['maint_content_crc']
                if str(crc) != str(crc2):
                    configuration['maint_content_crc'] = str(crc)
                    f = open(f"./resources/{ver}_config.json", 'w')
                    f.write(json.dumps(configuration))
                    f.close()
                    if len(re.findall('<\s*span style="color:#131665"[^>]*>(.*?)<\s*\/\s*span>',
                                      maint['apiData']['contents'])) > 0:
                        deliver(ver, clean_note(ver,
                                                 re.findall(
                                                     '<\s*span style="color:#131665"[^>]*>(.*?)<\s*\/\s*span>',
                                                     maint['apiData']['contents'])[0]) + end_time, None)
                    elif len(re.findall('<\s*span style="color:#dd5d65"[^>]*>(.*?)<\s*\/\s*span>',
                                        maint['apiData']['contents'])) > 0:
                        deliver(ver, clean_note(ver,
                                                 re.findall(
                                                     '<\s*span style="color:#DD5d65"[^>]*>(.*?)<\s*\/\s*span>',
                                                     maint['apiData']['contents'])[0]) + end_time, None)
                    elif len(re.findall('<\s*span style=""color:#DD5D65""[^>]*>(.*?)<\s*\/\s*span>',
                                        maint['apiData']['contents'])) > 0:
                        deliver(ver, clean_note(ver,
                                                 re.findall(
                                                     '<\s*span style=""color:#DD5D65""[^>]*>(.*?)<\s*\/\s*span>',
                                                     maint['apiData']['contents'])[0]) + end_time, None)
                    elif len(re.findall('<\s*span class="bold" style="font-size:30px"[^>]*>(.*?)<\s*\/\s*span>',
                                        maint['apiData']['contents'])) > 0:
                        deliver(ver, clean_note(ver, re.findall(
                            '<\s*span class="bold" style="font-size:30px"[^>]*>(.*?)<\s*\/\s*span>',
                            maint['apiData']['contents'])[0]) + end_time, None)
                    else:
                        deliver(ver, f"[{str(ver).upper()}] Emergency Maintenance Notice" + end_time, None)
            else:
                deliver(ver, f"[{str(ver).upper()}] Maintenance time updated.\n(No contents to show)" + end_time, None)
    # check servers for new event banners
    if config.check_banners and ver == 'gb':
        print(Fore.LIGHTYELLOW_EX + f"[{str(ver).upper()}] checking event banners...")
        skip = json.loads(open('./resources/skip.json', 'r').read())
        num = ''
        for i in range(config.max_event_banners):
            if len(str(i)) == 1:
                num = '000' + str(i)
            if len(str(i)) == 2:
                num = '00' + str(i)
            if len(str(i)) == 3:
                num = '0' + str(i)
            # it is possible to request a better quality by changing the extension to ".png"
            # but this is not recommended because the game does not do this & could be monitored requests
            if i not in skip['regular'] and int(i) <= config.max_event_banners:
                r = requests.get(urls['banners'] + 'banner_s_regular_' + str(num) + '_en.aos',
                                 stream=True, allow_redirects=True)
                if r.status_code == 200:
                    f = open('./data/banner.aos', 'wb')
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                    f.close()
                    deliver(ver, f"[{str(ver).upper()}] Upcoming weekly event. `{num}`", 0)
                    skip['regular'].append(i)
            if i not in skip['irregular'] and int(i) <= config.max_event_banners:
                r = requests.get(urls['banners'] + 'banner_s_irregular_' + str(num) + '_en.aos',
                                 stream=True, allow_redirects=True)
                if r.status_code == 200:
                    f = open('./data/banner.aos', 'wb')
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                    f.close()
                    deliver(ver, f"[{str(ver).upper()}] Upcoming special event. `{num}`", 0)
                    skip['irregular'].append(i)
            if i not in skip['pickup'] and int(i) <= config.max_pickup_banners:
                r = requests.get(urls['banners'] + 'banner_s_pickup_' + str(num) + '_en.aos',
                                 stream=True, allow_redirects=True)
                if r.status_code == 200:
                    f = open('./data/banner.aos', 'wb')
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                    f.close()
                    deliver(ver, f"[{str(ver).upper()}] Upcoming summon event. `{num}`", 0)
                    skip['pickup'].append(i)
            if i not in skip['stepup'] and int(i) <= config.max_stepup_banners:
                r = requests.get(urls['banners'] + 'banner_s_stepup_' + str(num) + '_en.aos',
                                 stream=True, allow_redirects=True)
                if r.status_code == 200:
                    f = open('./data/banner.aos', 'wb')
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                    f.close()
                    deliver(ver, f"[{str(ver).upper()}] Upcoming stepup event. `{num}`", 0)
                    skip['stepup'].append(i)
        f = open('./resources/skip.json', 'w')
        f.write(json.dumps(skip))
        f.close()
    # check for new notice images
    if config.check_notices:
        print(Fore.LIGHTYELLOW_EX + f"[{str(ver).upper()}] checking notices...")
        skip_notices = json.loads(open('./resources/notices.json', 'r').read())
        notices = server.get_notices(ver)
        for i in notices:
            if i['listType'] == '3':
                if i['imgUrl'] not in skip_notices[ver]:
                    print(Fore.LIGHTCYAN_EX + '   -> ' + str(i['imgUrl']))
                    r = requests.get(i['imgUrl'], stream=True, allow_redirects=True)
                    if r.status_code == 200:
                        f = open('./data/notice.jpg', 'wb')
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                        f.close()
                        deliver(ver, f"[{str(ver).upper()}] New notice. `{str(i['imgUrl'].split('/')[7])}`", 1)
                        skip_notices[ver].append(i['imgUrl'])
        f = open('./resources/notices.json', 'w')
        f.write(json.dumps(skip_notices))
        f.close()
    # check for new singular notice images
    if config.check_singular_notices:
        print(Fore.LIGHTYELLOW_EX + f"[{str(ver).upper()}] checking singular notices...")
        skip_singular = json.loads(open('./resources/singleNotices.json', 'r').read())
        singular = server.get_singular_notices(ver, int(round(time.time() * 1000)))
        if singular is not None and 'apiData' in singular:
            if singular['apiData']['topBannerImage'] not in skip_singular[ver]:
                print(Fore.LIGHTCYAN_EX + '   -> ' + str(singular['apiData']['topBannerImage']))
                r = requests.get(singular['apiData']['topBannerImage'], stream=True, allow_redirects=True)
                if r.status_code == 200:
                    f = open('./data/notice.jpg', 'wb')
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                    f.close()
                    deliver(ver, f"[{str(ver).upper()}] New singular notice. (Top)\n`{str(singular['apiData']['topBannerImage'].split('/')[7])}`", 1)
                    skip_singular[ver].append(singular['apiData']['topBannerImage'])
            if singular['apiData']['bottomBannerImage'] not in skip_singular[ver]:
                print(Fore.LIGHTCYAN_EX + '   -> ' + str(singular['apiData']['bottomBannerImage']))
                r = requests.get(singular['apiData']['bottomBannerImage'], stream=True, allow_redirects=True)
                if r.status_code == 200:
                    f = open('./data/notice.jpg', 'wb')
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                    f.close()
                    deliver(ver, f"[{str(ver).upper()}] New singular notice. (Bottom)\n`{str(singular['apiData']['bottomBannerImage'].split('/')[7])}`", 1)
                    skip_singular[ver].append(singular['apiData']['bottomBannerImage'])
        f = open('./resources/singleNotices.json', 'w')
        f.write(json.dumps(skip_singular))
        f.close()
    # check for new bmdata to download
    if config.check_data:
        print(Fore.LIGHTYELLOW_EX + f"[{str(ver).upper()}] checking data-download...")
        new_version = ''
        # "m" includes items, shop bundles, cosmetics, character art, icons, backgrounds & so on
        # "enu" is only for global; it includes some default event banners & all summon banners
        # all other event banners are stored on the servers (summon banners removed on global servers)
        r = requests.get(urls['configuration'], allow_redirects=True)
        configuration_json = r.json()
        patch = configuration['relative_sub']
        previous_patch = configuration['previous_sub']
        patch_version = configuration['version']
        previous_version = configuration['previous_version']
        # we have to make sure it's not previous due to multiple requests overtime
        if str(previous_patch) != str(configuration_json['patch']['android']['relative_sub']) and str(patch) != str(
                configuration_json['patch']['android']['relative_sub']):
            configuration['relative_sub'] = configuration_json['patch']['android']['relative_sub']
            previous_patch = patch
            configuration['previous_sub'] = previous_patch
            patch = configuration['relative_sub']
            print(patch)
        if str(configuration_json['patch']['android']['version']) not in previous_version and str(
                patch_version) != str(configuration_json['patch']['android']['version']):
            configuration['version'] = configuration_json['patch']['android']['version']
            previous_version = patch_version
            configuration['previous_version'].append(previous_version)
            new_version = configuration['version']
            print(new_version)
        else:
            for v in range(10):
                if v != 0:
                    t = server.ticks(datetime.datetime.utcnow())
                    r = requests.get(urls['data'] + str(patch) + '/' + str(
                        int(patch_version) + int(v)) + '/m/bmdata?t=' + str(int(t)), stream=True,
                                     allow_redirects=True)
                    if r.status_code == 200:
                        new_version = str(int(patch_version) + int(v))
                        break
                    elif config.failed_versions and r.status_code == 403:
                        print('403 - Forbidden: ' + str(int(patch_version) + int(v)))
                    elif config.failed_versions and r.status_code == 404:
                        print('404 - Not found: ' + str(int(patch_version) + int(v)))
        if str(new_version) != '' and str(patch_version) != str(new_version):
            print('200 - Found: ' + new_version)
            patch_version = new_version
            configuration['version'] = patch_version
            f = open(f"./resources/{ver}_config.json", 'w')
            f.write(json.dumps(configuration))
            f.close()
            if config.discord_patch_info:
                deliver(ver,
                        '<:gem:585340092634234880> **Data-download** <:gem:585340092634234880>\n```Phase: ' + str(
                            patch) + '\nVersion: ' + str(patch_version) + '```', None)
            for i in folders:
                if not fs.path.isdir(f"./data/{ver}/{i}"):
                    fs.mkdir(f"./data/{ver}/{i}")
                bmdata = server.get_folder_data(ver, patch, patch_version, i)
                if bmdata and fs.path.isfile(f"./data/{ver}/{i}_bundles3.txt"):
                    if fs.path.isfile(f"./data/{ver}/{i}.txt"):
                        fresh_folder = False
                    else:
                        fresh_folder = True
                    f = open(f"./data/{ver}/{i}_bundles3.txt", 'r')
                    txt = f.read()
                    f.close()
                    if not fs.path.isfile(f"./data/{ver}/{i}-ticks.txt"):
                        open(f"./data/{ver}/{i}-ticks.txt", 'w').close()
                    ticks = open(f"./data/{ver}/{i}-ticks.txt", 'r').read().split('\n')
                    zip_names = txt.split('\n')
                    sorted_zips = []
                    for x in zip_names:
                        if x in zip_names:
                            if len(x) == 19:
                                x = str(x[:18])
                                sorted_zips.append(x)
                            if len(x) == 18:
                                sorted_zips.append(x)
                    max_dl = len(sorted_zips)
                    min_dl = 1
                    for x in sorted_zips:
                        if x not in ticks:
                            if config.download_progress:
                                print(f"[{min_dl}/{max_dl}]")
                                min_dl = min_dl + 1
                            f = open(f"./data/{ver}/{i}-ticks.txt", 'a')
                            f.write(x + '\n')
                            f.close()
                            if not fs.path.isfile(f"./data/{ver}/{str(i)}/{str(x)}.zip"):
                                zipped = server.get_assets(ver, patch, patch_version, i, x)
                                if zipped:
                                    # unzip, organize, filter
                                    ZipFile(f"./data/{ver}/{str(i)}/{str(x)}.zip", 'r').extractall(f"./data/{ver}/{str(i)}/{str(x)}/")
                                    if fresh_folder:
                                        unpack_all_assets(ver, f"./data/{ver}/{str(i)}/{str(x)}/", f"./data/{ver}/{str(i)}/")
                                    else:
                                        unpack_new_assets(ver, f"./data/{ver}/{str(i)}/{str(x)}/", f"./data/{ver}/{str(i)}/")
                                    fs.unlink(f"./data/{ver}/{str(i)}/{str(x)}.zip")
                                    shutil.rmtree(f"./data/{ver}/{str(i)}/{str(x)}")
                                else:
                                    print('[!] no zip')
                else:
                    print('[!] no bmdata')
            if config.discord_object_names:
                for f in fs.listdir(f"./data/{ver}/overview/"):
                    deliver(ver, 'Overview of **Updated** Object(s) in Data-Download.', 0,
                            f"./data/{ver}/overview/{str(f)}")
                    fs.unlink(f"./data/{ver}/overview/{str(f)}")
    print('------------------------')


# an endless timed loop that calls a func to do requests.
async def loop_process():
    if config.check_global:
        begin_poll('gb')
    if config.check_japan:
        begin_poll('jp')
    if config.check_korean:
        begin_poll('kr')
    await asyncio.sleep(config.check_time * 60)
    await loop_process()

loop.run_until_complete(loop_process())
