# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

from datetime import datetime
from parladata_base_api.storages.storage import DataStorage
from parladata_base_api.storages.session_storage import Session
from parladata_base_api.storages.agenda_item_storage import AgendaItem

from parser_zagreb.spiders.session_notes_spider import NotesSpider
from parser_zagreb.spiders.votes_spider import VotesSpider
from parser_zagreb.spiders.questions_spider import QuestionsSpider
from parser_zagreb.spiders.members_spider import MembersSpider

from parser_zagreb.data_parsers.session_note_parser import SessionNotesParser
from parser_zagreb.data_parsers.votes_parser import VotesParser
from parser_zagreb.data_parsers.questions_parser import QuestionsParser
from parser_zagreb.data_parsers.member_parser import MemberParser

from parser_zagreb.settings import MANDATE, MANDATE_STARTIME, MAIN_ORG_ID, API_URL, API_AUTH


import logging
logger = logging.getLogger('pipeline logger')

class ParserZagrebPipeline:
    mandate_start_time = datetime(day=1, month=12, year=2020)
    def __init__(self):
        self.storage = DataStorage(
            MANDATE, MANDATE_STARTIME, MAIN_ORG_ID, API_URL, API_AUTH[0], API_AUTH[1]
        )
        Session.keys = ["mandate", "name"]
        AgendaItem.keys = ["name", "session"]

    def process_item(self, item, spider):
        logger.debug(type(item))
        logger.debug(type(spider))
        if isinstance(spider, NotesSpider):
            SessionNotesParser(item, self.storage)
        elif isinstance(spider, VotesSpider):
            VotesParser(item, self.storage)
        elif isinstance(spider, QuestionsSpider):
            QuestionsParser(item, self.storage)
        elif isinstance(spider, MembersSpider):
            MemberParser(item, self.storage)
        else:
            return item
