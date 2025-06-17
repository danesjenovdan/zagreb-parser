import re
from datetime import datetime, timedelta
from enum import Enum
from os import listdir
from os.path import isfile, join

from docx2python import docx2python


class ParserState(Enum):
    HEADER = 1
    PERSON = 2
    CONTENT = 3
    VOTE = 4


class SpeechesParser(object):
    def __init__(self, data_storage, session_id=None):
        self.data_storage = data_storage
        path = "files/transkripti"
        if session_id:
            transcript_files = [f"Fonogram.{session_id}.docx"]
        else:
            transcript_files = [f for f in listdir(path) if isfile(join(path, f))]
            transcript_files.sort()

        for file_name in transcript_files:

            print(file_name)
            with docx2python(f"{path}/{file_name}") as docx_content:
                self.document = docx_content.text.split("\n")
                self.parse(file_name)

    def parse(self, file_name):

        session_day = 0
        session_no = file_name.split(".")[1].lstrip("0")
        if "_" in session_no:
            session_no, session_day = session_no.split("_")
        session_name = f"{session_no}. sjednica Gradske skupštine Grada Zagreba"
        session = self.data_storage.session_storage.get_or_add_object(
            {
                "name": session_name,
                "organization": self.data_storage.main_org_id,
                "organizations": [self.data_storage.main_org_id],
                "in_review": False,
                "classification": "regular",
                "mandate": self.data_storage.mandate_id,
            }
        )

        print(session.start_time)
        start_time = datetime.fromisoformat(session.start_time) + timedelta(
            days=int(session_day)
        )
        print(start_time)
        print(session.name)

        self.speeches = []
        current_person = None
        current_text = ""
        state = ParserState.HEADER
        # reset speech count
        session.count = None
        order = session.get_speech_count() + 1
        for paragraph in self.document:
            text = paragraph.strip()
            if self.skip_line(text):
                continue

            if text.startswith("Sjednica je završena u"):
                break

            name = self.parse_name_from_line(text)

            if name and state in [ParserState.HEADER, ParserState.CONTENT]:
                person = self.data_storage.people_storage.get_or_add_object(
                    {"name": name.strip()}
                )
                state = ParserState.CONTENT
                if current_text:

                    fixed_text = self.fix_speech_content(current_text)
                    self.speeches.append(
                        {
                            "speaker": current_person.id,
                            "content": fixed_text.strip(),
                            "session": session.id,
                            "order": order,
                            "start_time": (
                                start_time + timedelta(seconds=order)
                            ).isoformat(),
                        }
                    )
                    current_person = person
                    current_text = ""
                    order += 1
                else:
                    current_person = person

            elif state == ParserState.CONTENT:
                if not current_text and text.startswith("-"):
                    text = text.lstrip("-").strip()
                current_text += f"{text}\n"

        # save last speech
        fixed_text = self.fix_speech_content(current_text)
        self.speeches.append(
            {
                "speaker": current_person.id,
                "content": fixed_text.strip(),
                "session": session.id,
                "order": order,
                "start_time": (start_time + timedelta(minutes=order)).isoformat(),
            }
        )

        session.add_speeches(self.speeches)

    def skip_line(self, text):
        if text.startswith("……"):
            return True
        elif not text:
            return True
        elif text.startswith("* * * * *"):
            return True
        return False

    def fix_speech_content(self, content):
        repalce_chars = [("«", '"'), ("»", '"')]
        for org_char, rapcece_char in repalce_chars:
            content = content.replace(org_char, rapcece_char)

        return content

    def parse_name_from_line(self, line):
        name = re.search(r"([A-ZČŽŠĐĆÖ -]*)( iz klupe)?:$", line)
        if name:
            return name.group(1)
        else:
            return None
