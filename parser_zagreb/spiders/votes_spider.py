import json
import re
from datetime import datetime

import requests
import scrapy


class VotesSpider(scrapy.Spider):
    name = "votes"
    base_url = "https://web.zagreb.hr"
    start_urls = [
        "https://web.zagreb.hr/sjednice/2021/sjednice_skupstine_2021.nsf/web_pretraga_autoriziran_font_new?OpenForm"
    ]

    def parse(self, response):
        sessions = response.css("select[name='rb_sjednice']>option::text").extract()
        for session in reversed(sessions):
            url = f"https://web.zagreb.hr/sjednice/2021/sjednice_skupstine_2021.nsf/DRJ?OpenAgent&{session.strip()}"
            yield scrapy.Request(
                url=url,
                callback=(self.parse_session),
            )

    def parse_session(self, response):
        text_with_session_name = (
            response.css("table")[0].css("tr")[2].css("::text").extract_first().strip()
        )
        for link in response.css("a.nav::attr(href)").extract():
            yield scrapy.Request(
                url=f"{self.base_url}{link}",
                callback=(self.parser_vote),
                meta={"session_text": text_with_session_name},
            )

    def parser_vote(self, response):
        vote_name = response.css("td>b>font::text").extract()
        champion = response.css("td>font::text").extract()
        no_agenda = "".join(response.css("td::text").extract()).strip()

        links = []
        dom_links = response.css("a")
        for link in dom_links:
            href = link.css("::attr(href)").extract_first()
            if href == "#":
                onclick = link.css("::attr(onclick)").extract_first()
                path = onclick.split("'")[1]
                href = f"{self.base_url}{path}"
            text = link.css("font::text").extract_first()
            links.append({"href": href, "text": text.strip()})

        yield {
            "vote_name": vote_name,
            "champion": champion,
            "links": links,
            "session_text": response.meta["session_text"],
            "no_agenda": no_agenda,
            "url": response.url,
        }
