import scrapy
from slugify import slugify

from parser_zagreb.items import MembershipItem


class MembershipsSpider(scrapy.Spider):
    name = "memberships"
    base_url = "https://skupstina.zagreb.hr"
    start_urls = ["https://skupstina.zagreb.hr/klubovi/32"]

    def parse(self, response):
        for url in response.css("div.page-text a::attr(href)").extract():
            yield scrapy.Request(
                url=f"{self.base_url}{url}",
                callback=(self.parse_club),
            )

    def parse_club(self, response):
        roles = response.css("div.page-text tr")
        club_name = response.css("div.page-content h1::text").extract_first().strip()
        for role in roles:
            role_members = []
            members = role.css("td strong::text").extract()
            print(members)
            if members:
                role_text = members[0].strip()
                role_members =  [member.strip() for member in members[1:]]
            else:
                members = role.css("td::text").extract()
                if members:

                    role_text = members[0].strip()
                    role_members = [member.strip() for member in members[1:]]
                    print(role_members)
            for name in role_members:
                print({
                    "name": name,
                    "club_name": club_name,
                    "role_text": role_text,
                })
                # yield {
                    # "name": name,
                    # "club_name": club_name,
                    # "role_text": role_text,
                # }
                yield MembershipItem(
                    name=name.strip(),
                    organization=club_name.strip(),
                    role=role_text.strip(),
                )
