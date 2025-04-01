# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SessionNoteItem(scrapy.Item):
    url = scrapy.Field()
    text = scrapy.Field()


class VoteItem(scrapy.Item):
    vote_name = scrapy.Field()
    champions = scrapy.Field()
    links = scrapy.Field()
    session_text = scrapy.Field()
    no_agenda = scrapy.Field()
    url = scrapy.Field()
    url_text = scrapy.Field()
    order = scrapy.Field()

class QuestionItem(scrapy.Item):
    author = scrapy.Field()
    recipient = scrapy.Field()
    title = scrapy.Field()
    links = scrapy.Field()
    url = scrapy.Field()
    session_text = scrapy.Field()

class MemberItem(scrapy.Item):
    name = scrapy.Field()
    committee = scrapy.Field()
    party = scrapy.Field()