#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import time

from bs4 import BeautifulSoup
from bs4 import SoupStrainer

proxies = {
  "http": "http://localhost:3128",
  "https": "http://localhost:3128",
}

proxy_support = urllib2.ProxyHandler(proxies)
opener = urllib2.build_opener(proxy_support)
urllib2.install_opener(opener)

def scrape_app_categories():
    url = 'https://play.google.com/store/apps'

    soup = BeautifulSoup(urllib2.urlopen(url), "lxml")

    categories = soup.find('div', {'class': 'action-bar-dropdown-children-container'})
    games = categories.find('a', {'href': '/store/apps/category/GAME'}).parent.parent
    
    for div in games.find_all('div', {'class': 'child-submenu-link-wrapper'}):
        print div.a.get('href')
        print div.a.get('title')
