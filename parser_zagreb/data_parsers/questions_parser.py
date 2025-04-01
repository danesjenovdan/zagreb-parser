import logging
import re

from .base_parser import BaseParser

logger = logging.getLogger("session logger")


class QuestionsParser(BaseParser):
    def __init__(self, item, storage):
        """
        {
            "author": ["Gradski zastupnik:", " ", "Ivica Lovrić", "Nestranački", " "],
            "title": ["Zaduženost Zagrebačkog holdinga d.o.o.", "Pisani odgovor Uprave trgovačkog  društva Zagrebačkog holdinga d.o.o."],
            "links": [{
                "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/C2B0EA08903C1C2AC12588F6004CDF96/$FILE/Ivica Lovrić_zaduženost Zagrebačkog holdinga d.o.o..pdf",
                "text": "PITANJE U PISANOM OBLIKU"
                }
                , {
                "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/FAEF401FB31B9A77C125893D0025AAF2/$FILE/02 Odgovor na pitanje.pdf",
                "text": "ODGOVOR NA PITANJE"
                }
            ],
            "url": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/PITANJE_WEB?OpenForm&ParentUNID=5A96B3E8B28C4C1CC12588F6004C80B0&font=14"
        }
        """
        # call init of parent object
        super(QuestionsParser, self).__init__(storage)
        logger.info(".:QUESTION PARSER:.")

        person = self.storage.people_storage.get_or_add_object(
            {
                "name": item["author"][2],
            }
        )

        if item["author"][3] == "Nestranački":
            organization = None
        else:
            organization = self.storage.organization_storage.get_or_add_object(
                {
                    "name": item["author"][3],
                }
            )

        gov_id = re.search(r"ParentUNID=(.*?)(&|TARGET)", item["url"]).group(1)

        question_data = {
            "type_of_question": "question",
            "gov_id": gov_id,
            "mandate": self.storage.mandate_id,
            "title": item["title"][0],
            "person_authors": [person.id],
            "recipient_text": item["recipient"][1],
        }

        if organization:
            question_data["organization_authors"] = [organization.id]

        if item["session_text"]:

            session_text = item.get("session_text")[0].strip().strip(".")

            organization = self.storage.organization_storage.get_or_add_object(
                {
                    "name": self.parse_organization(session_text),
                }
            )

            session = storage.session_storage.get_or_add_object(
                {
                    "name": self.parse_session_name(session_text),
                    "organization": organization.id,
                    "organizations": [organization.id],
                    "in_review": False,
                    "classification": "regular",
                    "mandate": storage.mandate_id,
                }
            )
            if session.start_time:
                question_data["tiestamp"] = session.start_time.isoformat()
            question_data["session"] = session.id

        question = self.storage.question_storage.get_or_add_object(question_data)

        # send link
        if question.is_new and item["links"]:
            for link in item["links"]:
                if link["url"]:
                    link["question"] = question.id
                    link["url"] = link["url"].replace(" ", "+")
                    self.storage.parladata_api.links.set(link)

    def parse_session_name(self, text):
        no_session = re.search(r"(\d+).", text).group(1)
        return re.search(r"([0-9]{1,2})(\. sjednica) ([a-zA-Zš ]*)", text).group(0)

    def parse_organization(self, text):
        return re.search(r"([0-9]{1,2})(\. sjednica) ([a-zA-Zš ]*)", text).group(3)
