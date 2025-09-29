import scrapy

from parser_zagreb.items import SessionNoteItem


class NotesSpider(scrapy.Spider):
    name = "notes"
    base_url = "https://web.zagreb.hr"
    start_urls = [
        "https://web.zagreb.hr/sjednice/2025/sjednice_skupstine_2025.nsf/zapisnik?OpenAgent"
    ]

    def parse(self, response):
        for link in reversed(response.css("a.nav")):
            href = link.css("::attr(href)").extract_first()

            yield SessionNoteItem(
                url=f"{self.base_url}{href}",
                text=link.css("font::text").extract_first().strip(),
            )
