import scrapy

from parser_zagreb.items import QuestionItem


class QuestionsSpider(scrapy.Spider):
    name = "questions"
    base_url = "https://web.zagreb.hr"
    start_urls = [
        "https://web.zagreb.hr/sjednice/2021/sjednice_skupstine_2021.nsf/web_pitanja_van_sjednice?OpenAgent",
        "https://web.zagreb.hr/sjednice/2021/sjednice_skupstine_2021.nsf/web_pretraga_autoriziran_font_new?OpenForm",
    ]

    def parse(self, response):
        sessions = response.css("select[name='rb_sjednice_1']>option::text").extract()
        if sessions:
            for session in reversed(sessions):
                url = f"https://web.zagreb.hr/Sjednice/2021/SkupstinaZapisi_2021.nsf/web_pitanja?OpenAgent&{session.strip()}."
                yield scrapy.Request(
                    url=url,
                    callback=(self.parse_single_session),
                )
        else:
            for link in response.css("a.nav"):
                link = link.css("::attr(href)").extract_first()
                yield scrapy.Request(
                    url=f"{self.base_url}{link}",
                    callback=(self.question_parser),
                )

    def parse_single_session(self, response):
        session_name = response.css("body>table>tr")[1].css("td::text").extract()
        for link in response.css("a.nav"):
            link = link.css("::attr(href)").extract_first()
            yield scrapy.Request(
                url=f"{self.base_url}{link}",
                callback=(self.question_parser),
                meta={"session_name": session_name},
            )

    def question_parser(self, response):
        author = response.css("div[align='right'] font::text").extract()
        recipient = response.css(
            "tr[valign='top']>td>table>tr>td>i> font::text"
        ).extract()
        texts = response.css("tr[valign='top']>td>font::text").extract()
        links = []
        dom_links = response.css("a")
        print(dom_links)
        for link in dom_links:
            href = link.css("::attr(href)").extract_first()
            if href == "#":
                onclick = link.css("::attr(onclick)").extract_first()
                path = onclick.split("'")[1]
                href = f"{self.base_url}{path}"
            text = link.css("font::text").extract_first()
            links.append({"url": href, "text": text.strip()})

        yield QuestionItem(
            author=author,
            recipient=recipient,
            title=texts,
            links=links,
            url=response.url,
            session_text=response.meta.get("session_name"),
        )
