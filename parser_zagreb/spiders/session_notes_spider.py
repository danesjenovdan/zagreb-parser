import json
import re
from datetime import datetime

import requests
import scrapy


class NotesSpider(scrapy.Spider):
    name = "notes"
    base_url = "https://web.zagreb.hr"
    start_urls = [
        "https://web.zagreb.hr/sjednice/2021/sjednice_skupstine_2021.nsf/zapisnik?OpenAgent"
    ]

    def parse(self, response):
        for link in response.css("a.nav"):
            href = link.css("::attr(href)").extract_first()

            yield {
                "href": f"{self.base_url}{href}",
                "text": link.css("font::text").extract_first().strip(),
            }
