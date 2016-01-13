import platform
import os
import urllib.request
from urllib.request import URLError
import re
import sys
from subprocess import call
from io import BytesIO
import zipfile
import shutil

import config

__author__ = 'ohaz'

cs2d_path = config.cs2d_path
check_url = 'http://www.unrealsoftware.de/game_cs2d.php'
system_os = platform.system()
TEMP_FOLDER_NAME = 'downloader_temp'

FILES_TO_COPY = {'windows': ['CounterStrike2D.exe', os.path.join('sys', 'core', 'version.cfg')],
                 'linux': ['CounterStrike2D'],
                 'macos': []}

force_update = False


def run_subprocess(cmd):
    call(cmd)


def run_cs2d():
    runner = {'windows': run_cs2d_windows, 'linux': run_cs2d_linux}
    runner[system_os.lower()]()


def run_cs2d_windows():
    run_subprocess([os.path.join(cs2d_path, 'CounterStrike2D.exe')])


def run_cs2d_linux():
    run_subprocess(['chmod', '+x', 'CounterStrike2D'])
    run_subprocess([os.path.join(cs2d_path, 'CounterStrike2D')])


def download_to_temp(tokens, name):
    with urllib.request.urlopen(tokens[name]) as response:
            zip_data = BytesIO()
            zip_data.write(response.read())
            zip_file = zipfile.ZipFile(zip_data)
            if os.path.exists(os.path.join(cs2d_path, TEMP_FOLDER_NAME, name)):
                os.rename(os.path.join(cs2d_path, TEMP_FOLDER_NAME, name), os.path.join(cs2d_path, TEMP_FOLDER_NAME,
                                                                                        name + '_old'))
                shutil.rmtree(os.path.join(cs2d_path, TEMP_FOLDER_NAME, name + '_old'))
            os.mkdir(os.path.join(cs2d_path, TEMP_FOLDER_NAME, name))
            zip_file.extractall(os.path.join(cs2d_path, TEMP_FOLDER_NAME, name))


def main():

    print('Creating temp folders')
    try:
        if os.path.exists(cs2d_path) and not os.path.exists(os.path.join(cs2d_path, TEMP_FOLDER_NAME)):
            os.mkdir(os.path.join(cs2d_path, TEMP_FOLDER_NAME))
    except OSError as e:
        print('Wrong CS2D Path', file=sys.stderr)
        exit()

    try:
        with open(os.path.join(cs2d_path, 'sys', 'core', 'version.cfg')) as f:
            version = f.read()
            splits = version.split(' ')
            v_index = 0
            if len(splits) > 1:
                v_index = 1
            version = splits[v_index].rstrip()
    except IOError as e:
        print('Wrong CS2D Path', file=sys.stderr)
        exit()

    try:
        with urllib.request.urlopen(check_url) as response:
            html = response.read()
            m = re.search('Version: <b>([^\s]*)\s*(.*?)</b>', str(html))
            online_version = m.group(2)
    except URLError as e:
        print('Could not connect to online service (%s)' % e, file=sys.stderr)
        exit()
    except AttributeError as e:
        print('Could not connect to online service (%s)' % e, file=sys.stderr)
        exit()

    local_version_splits = version.split('.')
    online_version_splits = online_version.split('.')

    print('Local: ', version)
    print('Online: ', online_version)

    if not force_update:

        for k, v in enumerate(local_version_splits):
            if int(v) == int(online_version_splits[k]):
                continue
            break
        else:
            print('Local up to date. Starting cs2d...')
            run_cs2d()
            exit()

    print('Local too old. Have to update...')

    try:
        with urllib.request.urlopen('http://cs2d.com/download.php') as response:
            print('Getting basic download URLs')
            html = response.read()
            m_iter = re.finditer('<a href="(http://www\.unrealsoftware\.de/get\.php\?get=[^"]*\.zip)', str(html))
            to_search = []
            for m in m_iter:
                to_search.append(m.group(1))
            print('Getting download tokens')
            tokens = {}
            for url in to_search:
                with urllib.request.urlopen(url) as response_to_search:
                    html = response_to_search.read()
                    m = re.search('<a class="l_dl" href="get\.php\?get=(\w*?\.zip)&amp;p=1&amp;cid=([0-9]*?)">',
                                  str(html))
                    token_os = ''
                    if 'win' in m.group(1):
                        token_os = 'windows'
                    elif 'linux' in m.group(1):
                        token_os = 'linux'
                    elif 'macos' in m.group(1):
                        token_os = 'macos'
                    else:
                        print('What OS is ', m.group(1), 'supposed to be?')
                    tokens[token_os] = 'http://www.unrealsoftware.de/get.php?get=%s&p=1&cid=%s' % \
                                       (m.group(1), m.group(2))
    except URLError as e:
        print('Could not connect to online service (%s)' % e, file=sys.stderr)
        exit()
    except AttributeError as e:
        print('Could not connect to online service (%s)' % e, file=sys.stderr)
        exit()

    print('Downloading Files')

    download_to_temp(tokens, 'windows')
    for item in FILES_TO_COPY['windows']:
        print('Copying:', item, 'from', os.path.join(cs2d_path, TEMP_FOLDER_NAME, 'windows', item),
              'to', os.path.join(cs2d_path, item))
        if os.path.exists(os.path.join(cs2d_path, item)):
            os.remove(os.path.join(cs2d_path, item))
        shutil.copy(os.path.join(cs2d_path, TEMP_FOLDER_NAME, 'windows', item), os.path.join(cs2d_path, item))
    if system_os.lower() == 'linux':
        download_to_temp(tokens, 'linux')
        for item in FILES_TO_COPY['linux']:
            shutil.copy(os.path.join(cs2d_path, TEMP_FOLDER_NAME, 'linux', item), os.path.join(cs2d_path, item))
    elif system_os.lower() == 'macos':
        download_to_temp(tokens, 'macos')
        for item in FILES_TO_COPY['macos']:
            shutil.copy(os.path.join(cs2d_path, TEMP_FOLDER_NAME, 'macos', item), os.path.join(cs2d_path, item))

    print('Up to date now. Starting cs2d...')
    run_cs2d()

if __name__ == '__main__':
    main()
