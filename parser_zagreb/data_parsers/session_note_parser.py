import logging
import re

from .base_parser import BaseParser

logger = logging.getLogger("session logger")


class SessionNotesParser(BaseParser):
    def __init__(self, item, storage):
        """
        {
            "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/C18327DA4315296AC1258BF9003E47C6/$FILE/Zapisnik%2040.%20sjednice%20Gradske%20skupštine%20Grada%20Zagreba.pdf",
            "text": "Zapisnik sa 40. sjednice Gradske skupštine Grada Zagreba"
        },
        """
        # call init of parent object
        super(SessionNotesParser, self).__init__(storage)
        logger.info(".:SESSION NOTE PARSER:.")

        organization = self.storage.organization_storage.get_or_add_object(
            {
                "name": self.parse_organization(item.get("text")),
            }
        )

        logger.info(organization.id)

        session = storage.session_storage.get_or_add_object(
            {
                "name": self.parse_session_name(item.get("text")),
                "organization": organization.id,
                "organizations": [organization.id],
                "in_review": False,
                "classification": "regular",
                "mandate": storage.mandate_id,
            }
        )

        if session.is_new:
            self.storage.parladata_api.links.set(
                {
                    "session": session.id,
                    "url": item.get("url"),
                    "name": item.get("text"),
                    "note": item.get("text"),
                }
            )

    def parse_session_name(self, text):
        no_session = re.search(r"(\d+).", text).group(1)
        return f"{no_session}. sjednica Gradske skupštine Grada Zagreba"

    def parse_organization(self, text):
        return re.search(r"([0-9]{1,2})(\. sjednice) ([a-zA-Zš ]*)", text).group(3)
