import math
from functools import partial
import re
import logging
import selenium as se
import requests
import json
from time import sleep
from random import randint
from selenium import webdriver
# from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import config

logger = logging.getLogger()


class PageParser:
    chromedriver_path = config.chromedriver_path

    element_css_tags = {
        # Case page url
        "case_link": ".resultHeader.openCardLink",
        # Full case text is in file only
        "file_url": ".bigField"
    }
    
    re_pattern_id_from_url = "(?<=id=)(.*?)(?=&shard)"

    def __init__(self, url: str):
        self.url = url
        self.driver = webdriver.Chrome(self.chromedriver_path)  # "/var/chromedriver/chromedriver"
        sleep(5)
        self.driver.get(url)
        sleep(5)
        
    def get_elements_by_css_selector(self, element_name: str):
        css_tag = self.element_css_tags.get(element_name)
        elements = self.driver.find_elements(by=By.CSS_SELECTOR, value=css_tag)
        return list(elements)

    @property
    def page_count(self):
        """ Extract resulting cases count 
        and calculate page count assuming there are 10 cases per page """
        case_count_element = self.driver.find_element(by=By.ID, value="resultCount")
        case_count = case_count_element.text.split(' ')[-1][:-1]
        page_count = math.ceil(int(case_count)/10)
        return page_count

    @property
    def case_elemenets(self) -> list:
        """ List of web-elements containing case urls on current page  """
        return self.get_elements_by_css_selector("case_link")

    @staticmethod
    def get_url(element: se.webdriver.remote.webelement.WebElement) -> str:
        """ Extract url-string from web-element """
        return element.get_attribute("href")
    
    @property
    def current_page_case_urls(self) -> list:
        return list(map(self.get_url, self.case_elemenets))
    
    def extract_id(self, case_url: str):
        return re.search(self.re_pattern_id_from_url, case_url).group()     
    
    @property
    def current_page_case_ids(self) -> list:
        return list(map(self.extract_id, self.current_page_case_urls))
    
    @property
    def file_url(self):
        """ Case page 2-nd view, containing string fields only """
        return list(map(self.get_url, self.get_elements_by_css_selector("file_url")))[0]

    @staticmethod
    def get_case_json_dict(case_id: str) -> dict:
        resp = requests.post("https://bsr.sudrf.ru/bigs/showDocument.action", verify=False,
                             json={"request": {"id": case_id}},
                             headers={"Content-Type": "application/json"})
        json_dict = resp.json() 
        return json_dict
    
    @property
    def current_page_case_json_dicts(self) -> list:
        return list(map(self.get_case_json_dict, self.current_page_case_ids))
    
    def go_to_next_page(self):
        pass


class Case:
    def __init__(self, case_json):
        self.case_json = case_json
        self.case = case_json["document"]
        self.case_fields = self.case["fields"]
        
    def parse_field_kv(self, field_name: str, field_key: str):
        return field_name, self.case_fields[field_name[field_key]]
    
    @staticmethod
    def extract_values(field: dict) -> dict:
        target_values = ["value", "valueWOHL", "longValue", "dateValue"]
        return {v: field[v] for v in target_values}


if __name__ == "__main__":
    test_url = """https://bsr.sudrf.ru/bigs/portal.html#%7B%22start%22:0,%22rows%22:1000,%22uid%22:%22d7c55781-7685-44b9-9149-115cd9df3d01%22,%22type%22:%22MULTIQUERY%22,%22multiqueryRequest%22:%7B%22queryRequests%22:%5B%7B%22type%22:%22Q%22,%22request%22:%22%7B%5C%22mode%5C%22:%5C%22EXTENDED%5C%22,%5C%22typeRequests%5C%22:%5B%7B%5C%22fieldRequests%5C%22:%5B%7B%5C%22name%5C%22:%5C%22case_document_result_date%5C%22,%5C%22operator%5C%22:%5C%22B%5C%22,%5C%22query%5C%22:%5C%222018-01-01T00:00:00%5C%22,%5C%22sQuery%5C%22:%5C%222018-12-31T00:00:00%5C%22%7D,%7B%5C%22name%5C%22:%5C%22case_document_category_article_cat%5C%22,%5C%22operator%5C%22:%5C%22SEW%5C%22,%5C%22query%5C%22:%5C%22%D0%A1%D1%82%D0%B0%D1%82%D1%8C%D1%8F%20229.1%20%D0%A7%D0%B0%D1%81%D1%82%D1%8C%203%5C%22%7D%5D,%5C%22mode%5C%22:%5C%22AND%5C%22,%5C%22name%5C%22:%5C%22common%5C%22,%5C%22typesMode%5C%22:%5C%22AND%5C%22%7D%5D%7D%22,%22operator%22:%22AND%22,%22queryRequestRole%22:%22CATEGORIES%22%7D%5D%7D,%22sorts%22:%5B%7B%22field%22:%22score%22,%22order%22:%22desc%22%7D%5D,%22simpleSearchFieldsBundle%22:%22default%22,%22filterGroups%22:%5B%7B%22filterQueries%22:%5B%7B%22field%22:%22case_court_type%22,%22query%22:%22%D0%A0%D0%B0%D0%B9%D0%BE%D0%BD%D0%BD%D1%8B%D0%B9,%20%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D1%81%D0%BA%D0%BE%D0%B9,%20%D0%BC%D0%B5%D0%B6%D1%80%D0%B0%D0%B9%D0%BE%D0%BD%D0%BD%D1%8B%D0%B9%20%D1%81%D1%83%D0%B4%22,%22not%22:false%7D%5D,%22groupMode%22:%22OR%22,%22not%22:false%7D%5D,%22facet%22:%7B%22field%22:%5B%22type%22%5D%7D,%22facetLimit%22:21,%22additionalFields%22:%5B%22court_document_documentype1%22,%22court_case_entry_date%22,%22court_case_result_date%22,%22court_subject_rf%22,%22court_name_court%22,%22court_document_law_article%22,%22court_case_result%22,%22case_user_document_type%22,%22case_user_doc_entry_date%22,%22case_user_doc_result_date%22,%22case_doc_subject_rf%22,%22case_user_doc_court%22,%22case_document_category_article%22,%22case_user_doc_result%22,%22case_user_entry_date%22,%22m_case_user_type%22,%22m_case_user_sub_type%22,%22ora_main_law_article%22%5D,%22hlFragSize%22:1000,%22groupLimit%22:3,%22woBoost%22:false%7D\",\n"""
    search_page = PageParser(target_url)
    case_page_url = search_page.current_page_case_urls[0]
    case_page = PageParser(case_page_url)
    file_page = PageParser(case_page.file_url)
