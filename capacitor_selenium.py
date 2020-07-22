import os
import json

from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from pymongo import MongoClient


class CCapacitorParser:
    def __init__(self):
        self.total_pages = 0
        self.capacitors = []
        self.script = 'const setProperty = () => {     Object.defineProperty(navigator, "webdriver", ' \
                      '{       get: () => false,     }); }; setProperty();'
        dir_path = os.path.dirname(os.path.realpath(__file__))
        driver_path = os.path.join(dir_path, 'chromedriver')
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(executable_path=driver_path, chrome_options=options)
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
                print(e1)
                raise
        return self._db

    def send(self, cmd, params=None):
        resource = "/session/%s/chromium/send_command_and_get_result" % self.driver.session_id
        url = self.driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        self.driver.command_executor._request('POST', url, body)

    def parse(self, url):
        self.send("Page.addScriptToEvaluateOnNewDocument", params={"source": self.script})
        self.driver.get(url)

        table = WebDriverWait(self.driver, 120).until(ec.visibility_of_element_located(
            (By.XPATH, "/html/body/main/div/div/div[1]/div[6]/div/form/div[2]/div[2]/table/tbody")))

        for row in range(0, 25):
            capacitor = {
                'vendor_num': table.find_elements(By.CSS_SELECTOR, "div.mfr-part-num a")[row].text,
                'vendor': table.find_element(By.XPATH, "tr[%d]/td[4]/a" % (row + 1)).text,
                'descr': table.find_element(By.XPATH, "tr[%d]/td[5]/span" % (row + 1)).text,
                'capacity': table.find_element(By.XPATH, "tr[%d]/td[11]/span" % (row + 1)).text,
                'voltage': table.find_element(By.XPATH, "tr[%d]/td[12]/span" % (row + 1)).text,
                'dielectric': table.find_element(By.XPATH, "tr[%d]/td[13]/span" % (row + 1)).text,
                'deviation': table.find_element(By.XPATH, "tr[%d]/td[14]/span" % (row + 1)).text,
                'output_type': table.find_element(By.XPATH, "tr[%d]/td[15]/span" % (row + 1)).text,
            }
            self.save_capacitor(capacitor)

        if not self.total_pages:
            pages = self.driver.find_elements(By.CSS_SELECTOR, "ul.pagination li a")

            if len(pages) > 1:
                self.total_pages = int(pages[-2].text)

    def save_capacitor(self, capacitor):
        self.capacitors.append(capacitor)
        self.capacitor_collection.update_one(capacitor, {"$set": capacitor}, upsert=True)

    def process_capacitors(self):
        if self.capacitors:
            my_keys = [key for key in self.capacitors[0].keys() if key != '_id']
            for key in my_keys:
                unique_values = self.capacitor_collection.distinct(key)
                if unique_values:
                    my_filter = {
                        'name': key
                    }
                    param = {
                        'values': unique_values
                    }
                    self.capacitor_params_collection.update_one(my_filter, {"$set": param}, upsert=True)

    def show_results(self):
        print("------------------- RUSULTS --------------------")
        count = 0
        for document in self.capacitor_collection.find({}):
            print(document)
            count += 1
        print("%d capacitors found in mongoDB" % count)

        count = 0
        for document in self.capacitor_params_collection.find({}):
            print(document)
            count += 1
        print("%d parametres found in mongoDB" % count)



if __name__ == '__main__':
    cp = None
    start_url = 'https://ru.mouser.com/Passive-Components/Capacitors/Ceramic-Capacitors/_/N-5g8m'
    random_pages_num = 0

    try:
        cp = CCapacitorParser()
        cp.parse(start_url)

        if cp.total_pages:
            for i in range(0, random_pages_num):
                random_page = randint(1, cp.total_pages - 1)
                url_random_page = "{start_url}?No={page}".format(start_url=start_url, page=random_page * 25)
                cp.parse(url_random_page)

        print("{num} capacitors found".format(num=len(cp.capacitors)))
        cp.process_capacitors()
        cp.show_results()

    except Exception as e:
        print('Error during process %s' % e)
        raise e
    finally:
        if cp and cp.driver is not None:
            cp.driver.close()
