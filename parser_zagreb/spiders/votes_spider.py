import scrapy

from parser_zagreb.items import VoteItem


class VotesSpider(scrapy.Spider):
    name = "votes"
    base_url = "https://web.zagreb.hr"
    start_urls = [
        "https://web.zagreb.hr/sjednice/2021/sjednice_skupstine_2021.nsf/web_pretraga_autoriziran_font_new?OpenForm"
    ]

    def parse(self, response):

        session_id = getattr(self, "session_id", None)

        if not session_id:
            session_id = 1

        session_id = f"{session_id}."

        # sessions = response.css("select[name='rb_sjednice']>option::text").extract()
        # for session_id in list(reversed(sessions))[2:3]:
        url = f"https://web.zagreb.hr/sjednice/2021/sjednice_skupstine_2021.nsf/DRJ?OpenAgent&{session_id.strip()}"
        yield scrapy.Request(
            url=url,
            callback=(self.parse_session),
        )

    def parse_session(self, response):
        text_with_session_name = (
            response.css("table")[0].css("tr")[2].css("::text").extract_first().strip()
        )
        self.data = {"session_text": text_with_session_name, "votes": []}
        links = response.css("a.nav")
        self.total_links = len(links)
        for order, link in enumerate(links):
            href = link.css("::attr(href)").extract_first()
            text = link.css("::text").extract_first()
            print("BLA BLA")
            print(f"{self.base_url}{href}")
            yield scrapy.Request(
                url=f"{self.base_url}{href}",
                callback=(self.parser_vote),
                meta={"text": text, "order": order + 1},
            )

    def parser_vote(self, response):
        vote_name = response.css("td>b>font::text").extract()
        champions = response.css("td>font::text").extract()
        no_agenda = "".join(response.css("td::text").extract()).strip()
        no_agenda = no_agenda.replace("TOČKA: ", "").replace(".", "")

        links = []
        dom_links = response.css("a")
        for link in dom_links:
            href = link.css("::attr(href)").extract_first()
            if href == "#":
                onclick = link.css("::attr(onclick)").extract_first()
                path = onclick.split("'")[1]
                href = f"{self.base_url}{path}"
            text = link.css("font::text").extract_first()
            if text:
                links.append({"href": href, "text": text.strip()})

        self.data["votes"].append(
            VoteItem(
                vote_name=vote_name,
                champions=champions,
                links=links,
                no_agenda=no_agenda,
                url=response.url,
                url_text=response.meta["text"],
                order=response.meta["order"],
            )
        )
        if len(self.data["votes"]) == self.total_links:
            yield self.data
