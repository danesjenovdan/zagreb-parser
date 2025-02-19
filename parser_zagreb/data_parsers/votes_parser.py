from .base_parser import BaseParser

from datetime import datetime, timedelta

import requests
from pypdf import PdfReader

import logging, re


logger = logging.getLogger("session logger")


class VotesParser(BaseParser):
    def __init__(self, item, storage):
        """
        {
            "vote_name": ["Davanje prethodne suglasnosti na Prijedlog odluke o izmjenama Statuta Centra za kulturu i film Augusta Cesarca"],
            "champions": ["Upravno vijeće Centra za kulturu i film Augusta Cesarca", "Odbor za kulturu, međugradsku i međunarodnu suradnju i civilno društvo", "Odbor za Statut, Poslovnik i propise"],
            "links": [
            {
                "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/7AD39F407F4407C4C1258C20002D0760/$FILE/00 Dopis ureda.pdf",
                "text": "DOPIS GRADSKOG UREDA"
            }, {
                "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/54BE9F16DABE437EC1258C20002D0CD8/$FILE/01 Dopis predlagatelja.pdf",
                "text": "DOPIS PREDLAGATELJA"
            }, {
                "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/6AD1216C4D6FFCD7C1258C20002D1210/$FILE/Prijedlog odluke o izmjenama Statuta Statuta A. Cesarec 2025.pdf",
                "text": "PRIJEDLOG ODLUKE: o izmjenama Statuta"
            }, {
                "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/4771D0C19FB0DB25C1258C20002D5511/$FILE/STATUT-CKF A. Cesarec 2022.pdf",
                "text": "STATUT"
            }, {
                "href": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/0/A2F5F8F0152D4E3FC1258C20002D5D32/$FILE/Odluka-o-izmjenama-i-dopunama-Statuta-Centra_2024.pdf",
                "text": "ODLUKA: o izmjenama i dopunama 2024."
            }],
            "session_text": "41. sjednica Gradske skupštine Grada Zagreba, utorak 18.02.2025 u 09:00h, u Staroj gradskoj vijećnici, Ulica sv. Ćirila i Metoda 5/I., dvorana \"A\".",
            "no_agenda": "TOČKA: 10.",
            "url": "https://web.zagreb.hr/Sjednice/2021/sjednice_skupstine_2021.nsf/PW_NEW?OpenForm&ParentUNID=D2971AF9A26ED6DDC1258C20002CD136&font=14"
        }
        """
        # call init of parent object
        super(VotesParser, self).__init__(storage)
        logger.info(".:Vote PARSER:.")
        logger.debug(item)

        organization = self.storage.organization_storage.get_or_add_object({
            "name": self.parse_organization(item.get("session_text")),
        })

        self.session = storage.session_storage.get_or_add_object(
            {
                "name": self.parse_session_name(item.get("session_text")),
                "organization": organization.id,
                "organizations": [organization.id],
                "in_review": False,
                "classification": "regular",
                "mandate": storage.mandate_id,
            }
        )

        session_start_time = self.parse_start_time(item.get("session_text"))
        vote_name = item.get("vote_name")[0]

        if self.session.start_time is None:
            self.session.update_start_time(session_start_time)

        if not self.session.vote_storage.check_if_motion_is_parsed({
            "text": vote_name,
            "datetime": session_start_time.isoformat()
        }):
            order = self.get_order(item.get("no_agenda"))
            ai = self.session.agenda_items_storage.get_or_add_object({
                "datetime": (session_start_time + timedelta(minutes=int(order))).isoformat(),
                "name": item.get("no_agenda"),
                "session": self.session.id,
                "order": order,
                #"gov_id": item.get("url")
            })
            motion_data = {
                "session": self.session.id,
                "text": vote_name,
                "title": vote_name,
                "datetime": session_start_time.isoformat(),
                "epa": None,
                "law": None,
            }
            motion_obj = self.session.vote_storage.get_or_add_object(motion_data)
            for link in item.get("links"):
                logger.debug(link.get("href"))
                if link.get("text") == "POIMENIČNO GLASOVANJE I REZULTAT GLASOVANJA":
                    self.save_ballots(link.get("href"), motion_obj)
                self.storage.parladata_api.links.set(
                    {
                        "agenda_item": ai.id,
                        "motion": motion_obj.id,
                        "url": link.get("href").replace(" ", "+"),
                        "name": link.get("text"),
                        "note": link.get("text"),
                    }
                )

    def save_ballots(self, url, motion):
        if motion.is_new:
            ballots = BallotsPDFParser().parse_url(url).get_ballots()
            print("VoteParser", ballots)
            for ballot in ballots:
                voter = self.storage.people_storage.get_or_add_object({
                    "name": ballot.pop("name")
                })
                ballot["vote"] = motion.vote.id
                ballot["personvoter"] = voter.id
            for ballot in ballots:
                self.session.vote_storage.set_ballots(ballots)

    def parse_session_name(self, text):
        no_session = re.search(r"(\d+).", text).group(1)
        return re.search(r"([0-9]{1,2})(\. sjednica) ([a-zA-Zš ]*)", text).group(0)
    
    def parse_organization(self, text):
        return re.search(r"([0-9]{1,2})(\. sjednica) ([a-zA-Zš ]*)", text).group(3)
    
    def parse_start_time(self, text):
        groups = re.search(r"([0-9]{2}\.[0-9]{2}\.[0-9]{4})\su\s([0-9]{2}:[0-9]{2})h", text)
        return datetime.strptime(groups[0], "%d.%m.%Y u %H:%Mh")
    
    def get_order(self, text):
        return re.search(r"\d+", text).group(0)


class BallotsPDFParser():

    def parse_file(self, file_path):
        self.reader = PdfReader(file_path)
        for page in self.reader.pages:
            lines = page.extract_text(extraction_mode="layout").split("\n")
            self.parse_page(lines)

    def parse_url(self, url):
        response = requests.get(url)
        self.data = []
        with open("files/tmp_vote.pdf", "r+b") as f:
            f.write(response.content)

            self.reader = PdfReader(f)

            for page in self.reader.pages:
                lines = page.extract_text(extraction_mode="layout").split("\n")
                self.parse_page(lines)

    def get_ballots(self):
        return self.data

    def parse_page(self, page_lines):
        print("parsing page")
        self.state = "META"
        for line in page_lines:
            line = line.strip()#.replace("\x00", "")
            print(self.state, line, len(line))
            if self.state == "META":
                splited = line.strip().lower().split()
                print(splited)
                if splited and splited[0] == "ime":
                    if ("suzdržan" in splited or "suzdržano" in splited) and "protiv" in splited and "za" in splited:
                        self.option_indexes = self.get_options_order(line)
                        self.state = "BALLOTS"
            elif self.state == "BALLOTS":
                if line.strip() == "O":
                    continue
                elif line.strip() == "":
                    continue
                elif line.strip().startswith("Tiskano"):
                    return
                elif line[0] == " ":
                    self.state == "WEIRD_BALLOTS"
                    name = line.strip()
                else:
                    name = line.split(")")[0]
                    try:
                        name, party = name.split("(")
                        option = self.parse_option(line)
                    except ValueError:
                        items = re.split(r"\s+", line)
                        name = items[0]
                        party = None
                        option = self.parse_option(line)
                        
                    self.data.append({
                        "name": name,
                        "party": party,
                        "option": option
                    })
        print("PDF parser", self.data)

    def parse_option(self, line):
        try:
            position = line.index("   X")
        except:
            return "error"
        for option, index in self.option_indexes.items():
            if position in range(index-5, index+5):
                return option

    def parse_option_old(self, line):
        try:
            position = line.index("   X")
        except:
            return "error"
        self.option_indexes
        if position > 120:
            return "absent"
        elif position > 90:
            return "against"
        elif position > 70:
            return "abstain"
        else:
            return "for"

    def get_options_order(self, line):
        line = line.lower().replace("\x00", "")
        replace_words = [("2'687$1", "odsutan"), ("suzdržano", "suzdržan")]
        for word in replace_words:
            if word[0] in line:
                line = line.replace(word[0], word[1])
        indexes = {"za": None, "protiv": None, "suzdržan": None, "odsutan": None}
        for i in indexes.keys():
            indexes[i] = line.index(i)
        print(indexes)
        return indexes
