import time
import scrapy

from random import randint
from pymongo import MongoClient


class CapasitorSpider(scrapy.Spider):
    name = "capacitors"
    download_delay = 2
    rotate_user_agent = True

    def __init__(self):
        super(CapasitorSpider).__init__()
        self.pages_needed = 3
        self.pages_total = None
        self.capacitors = []
        self._db = None
        self.capacitor_collection = self.db.capacitor
        self.capacitor_params_collection = self.db.capacitor_params

    @property
    def db(self):
        if self._db is None:
            try:
                client = MongoClient('localhost', 27018)
                db = client.capacitor
                self._db = db
            except Exception as e1:
                self.log(e1)
                raise
        return self._db

    def start_requests(self):
        urls = [
            'https://ru.mouser.com/Passive-Components/Capacitors/Ceramic-Capacitors/_/N-5g8m'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, method='POST', meta={'dont_redirect': True,
                                                                                    'handle_httpstatus_list': [302]})

    def parse(self, response):
        filename = 'capacitor_{time}.html'.format(time=str(time.time()))
        with open(filename, 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)

        capacitors = response.xpath('/html/body/main/div/div/div[1]/div[6]/div/form/div[2]/div[2]/table/tbody/tr')

        for row in capacitors:
            capacitor = {
                'vendor_num': row.css('div.mfr-part-num a::text').get(),
                'vendor': row.xpath('td[4]/a/text()').get(),
                'descr': row.xpath('td[5]/span/text()').get(),
                'capacity': row.xpath('td[11]/span/text()').get(),
                'voltage': row.xpath('td[12]/span/text()').get(),
                'dielectric': row.xpath('td[13]/span/text()').get(),
                'deviation': row.xpath('td[14]/span/text()').get(),
                'output_type': row.xpath('td[15]/span/text()').get(),
            }
            yield capacitor
            self.save_capacitor(capacitor)

        self.log("CAPACITORS FOUND" if capacitors else "CAPACITORS NOT FOUND")
        self.pages_needed -= 1

        if self.pages_needed > 0:
            if not self.pages_total:
                pages = response.css('ul.pagination li a::text').getall()
                if pages and len(pages) > 1:
                    self.pages_total = int(pages[-2])
                else:
                    self.log("COULDN'T FIND NEXT PAGE")

            if self.pages_total:
                random_page = randint(1, self.pages_total - 1)
                url_random_page = "?No={}".format(random_page * 25)
                self.log("NEXT RANDOM PAGE URL = %s" % url_random_page)
                yield response.follow(url_random_page, callback=self.parse, meta={'dont_redirect': True,
                                                                                  'handle_httpstatus_list': [302]})
            else:
                self.show_results()
        else:
            self.process_capacitors()
            self.show_results()

    def save_capacitor(self, capacitor):
        self.capacitors.append(capacitor)
        self.capacitor_collection.update_one(capacitor, {"$set": capacitor}, upsert=True)

    def process_capacitors(self):
        if self.capacitors:
            my_keys = [key for key in self.capacitors[0].keys() if key != '_id']
            for key in my_keys:
                unique_values = self.capacitor_collection.distinct(key)
                if unique_values:
                    my_filter = {'name': key}
                    param = {'values': unique_values}
                    self.capacitor_params_collection.update_one(my_filter, {"$set": param}, upsert=True)

    def show_results(self):
        count = 0
        for document in self.capacitor_collection.find({}):
            print(document)
            count += 1
        self.log("%d capacitors found in mongoDB" % count)
        print("%d capacitors found in mongoDB" % count)

        count = 0
        for document in self.capacitor_params_collection.find({}):
            print(document)
            count += 1
        self.log("Capacitors have %d parametres" % count)
        print("Capacitors have %d parametres" % count)
