#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2
import time
import logging
import json
import datetime
import random

from bs4 import BeautifulSoup
from bs4 import SoupStrainer

import boto.sqs
from boto.sqs.message import Message

from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

proxies = {
  "http": "http://localhost:3128",
  "https": "http://localhost:3128",
}

proxy_support = urllib2.ProxyHandler(proxies)
opener = urllib2.build_opener(proxy_support)
urllib2.install_opener(opener)

conn = boto.sqs.connect_to_region("eu-west-1")
q = conn.create_queue('google-play-scraper', 360)

mongo_client = MongoClient('localhost', 27017)
db = mongo_client.google_play
apps = db.apps

def scrape(id):
    logging.info("scraping %s", id)

    url = 'https://play.google.com/store/apps/details?id=%s' % id 
    
    soup = BeautifulSoup(urllib2.urlopen(url))
    category = soup.find('a', {'class': 'document-subtitle category'})

    app = apps.find_one({'id': id})
    if not app:
        app = dict()
        app['id'] = id
    
    text = soup.find('div', {'itemprop': 'author'}).a.get_text()
    if text:
        app['author'] = text
    
    text = soup.find('meta', {'itemprop': 'ratingValue'}).get('content')
    if text:
        app['rating'] = text

    text = soup.find('div', {"class": "cover-container"}).find('img', {"class": "cover-image"}).get('src')
    if text:
        app['icon'] = text

    text = category.get('href')
    if text:
        app['category-id'] = text

    text =  category.get_text()
    if text:
        app['category-name'] = text

    text = soup.find('div', {"itemprop": "description"}).div.prettify()
    if text:
        app['description'] = text

    text = soup.find('div', {"class": "document-title"}).get_text(strip=True)
    if text:
        app['title'] = text

    apps.save(app)

    for link in soup.find('head').find_all('link', {'hreflang': True}):
        m = Message()
        m.set_body(json.dumps({'id': id, 'cc': link.get('hreflang'), 'url': link.get('href')}))
        status = q.write(m)

def scrape_localized(id, cc, url):
    logging.info("scraping %s (%s)", id, cc)

    soup = BeautifulSoup(urllib2.urlopen(url), "html5lib")
    
    app = apps.find_one({'id': id})
    if not app:
        app = dict()
        app['id'] = id
    
    if not app.get(cc):
        app[cc] = dict()

    text = soup.find('a', {'class': 'document-subtitle category'}).get_text()
    if text:
        app[cc]['category-name'] = text

    text = soup.find('div', {"itemprop": "description"}).div.prettify()
    if text:
        app[cc]['description'] = text

    text = soup.find('div', {"class": "document-title"}).get_text(strip=True)
    if text:
        app[cc]['title'] = text

    apps.save(app)

if __name__ == "__main__":
    while True:
        m = q.read()
        if m:
            request = json.loads(m.get_body())
            if not "cc" in request:
                scrape(request["id"])
            elif "cc" in request:
                scrape_localized(request['id'], request["cc"], request['url'])
            q.delete_message(m)
        time.sleep(random.randint(1, 180))
        
