import scrapy
from slugify import slugify

from parser_zagreb.items import MemberItem


class MembersSpider(scrapy.Spider):
    name = "members"
    base_url = "https://skupstina.zagreb.hr"
    start_urls = ["https://skupstina.zagreb.hr/gradski-zastupnici-31/31"]

    def parse(self, response):
        for url in response.css("div.page-text>a::attr(href)").extract():
            yield scrapy.Request(
                url=f"{self.base_url}{url}",
                callback=(self.parse_member),
            )

    def parse_member(self, response):
        name = response.css("div.page-content>h1::text").extract_first()

        texts = response.css("div.page-text ::text").extract()

        state = ""

        party = ""
        committees = []

        for line in texts:
            line = line.strip()
            if not line:
                continue
            # state parser
            elif line.startswith("Pripadnost političkoj stranci"):
                state = "party"

            elif line.startswith("Članstvo u radnim tijelima Gradske skupštine"):
                state = "committee"

            elif line.startswith("Kontakt"):
                state = "contact"

            elif line.startswith("Obrazovanje"):
                state = "education"

            elif line.startswith("Osobni podaci"):
                state = "personal"
            # content parser

            elif state == "party":
                party = line.strip()

            elif state == "committee":
                committees.append(line.strip())

        yield MemberItem(
            name=name,
            party=party,
            committee=committees,
        )
