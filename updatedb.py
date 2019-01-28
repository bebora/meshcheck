#!/usr/bin/env python3
from bs4 import BeautifulSoup
import json
import requests
import time
import logging
import sys
import traceback
from tinydb import TinyDB, Query
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


class SafeGet():
    def __init__(self):
        pass

    @staticmethod
    def get(*args, **kwargs):
        try:
            r = requests.get(*args, **kwargs)
        except Exception:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            time.sleep(2)
            try:
                r = requests.get(*args, **kwargs)
            except Exception:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                sys.exit()
        finally:
            return r


class MeshUpdater():
    def __init__(self, mesh_id=671):
        self.mesh_id = mesh_id

    def run(self):
        popup_request = SafeGet.get(
            'http://zcube.vip/index.php?route=zpn/popup_product/info'
            '&product_id={}'
            .format(self.mesh_id)
        )
        popup_html = BeautifulSoup(popup_request.text, 'lxml')
        choices = []
        color_div = popup_html \
            .find('div', attrs={'id': 'JpopColor'}) \
            .find('div', attrs={'class': 'col-xs-12'})
        for span in color_div.findAll('span'):
            choices.append(
                {
                    'value': span['data-value'],
                    'name': span.find('img')['title'].strip(),
                    'img_src': span.find('img')['src']
                                   .strip()
                                   .replace('70x70', '430x430')
                })
        if len(choices) == 0:
            logging.info("Nothing changed")
            return {'new': [], 'removed': []}
        db = TinyDB('colors.json')
        Color = Query()
        db.update({'valid': False, 'new': False})

        for item in choices:
            result = db.search(Color.name == item['name'])
            if result == []:
                item['valid'] = True
                item['new'] = True
                db.insert(item)
            else:
                db.update({'valid': True}, Color.name == item['name'])

        new = db.search(Color.new == True)
        removed = db.search(Color.valid == False)
        db.remove(Color.valid == False)
        return {'new': new, 'removed': removed}
