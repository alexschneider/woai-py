#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__  import print_function
import requests
from bs4 import BeautifulSoup
import sys
import re
from multiprocessing.dummy import Pool
import shutil
import ftplib
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2


def get_all_links():
    r = requests.get('http://www.world-of-ai.com/allpackages.php')
    soup = BeautifulSoup(r.text)
    tables = soup.body.find(class_='wrap', recursive=False).div.find_all('table', class_='bordered')
    tables.pop(0) # We don't care about the world of ai installers
    links = set()
    avsim = re.compile('AVSIM')
    for table in tables:
        for tr in table.find_all('tr', recursive=False):
            td = tr.find_all('td', recursive=False)[-1] # we just want the last column (the one with the link)
            link = td.find('a', text=avsim)
            if 'FSX: '  in td.text: # If there are both fsx and fs9 versions
                link = td.find(text='FSX: ').find_next_sibling('a', text=avsim)
            links.add((link.get('href'), link.get('title')))
    return links


def download_all_files(links, username, password):
    num_of_links = len(links)
    link_number = iter(range(1, num_of_links + 1))
    with requests.Session() as s:
        request_data = {
            'Location': '',
            'UserLogin': username,
            'Password': password
        }
        s.post('http://library.avsim.net/dologin.php', data=request_data)
        if 'LibraryLogin' not in s.cookies: # we didn't log in properly
            print('Login failed, please check credentials')
            sys.exit(1)
        pool = Pool(3) # AVSim only allows 3 concurrent downloads


        def get_link(link):
            print('Package {num:03d}/{total} downloaded'.format(num=next(link_number), total=num_of_links), end='\r')
            sys.stdout.flush()
            library_page = s.get(link[0])
            soup = BeautifulSoup(library_page.text)
            download_link = soup.body.find('a', href=re.compile('download.php'))
            if download_link:
                download_id = download_link.get('href').split('=')[-1] # get the download id
                opener = urllib2.build_opener() # requests doesn't support downloading as ftp :(
                opener.addheaders.append(('Cookie', 'LibraryLogin=' + s.cookies['LibraryLogin']))
                ai = opener.open('http://library.avsim.net/sendfile.php?Location=AVSIM&Proto=ftp&DLID='  + download_id)
                with open(link[1], 'wb') as f:
                    shutil.copyfileobj(ai, f)


        results = pool.map(get_link, links)
        pool.close()
        pool.join()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        try:
            input = raw_input
        except NameError:
            pass
        username = input('AVSim username: ')
        password = input('AVSim password: ')
    else:
        username, password = sys.argv[1:2]
    all_links = get_all_links()
    download_all_files(all_links, username, password)
