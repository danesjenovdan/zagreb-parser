from .base_parser import BaseParser

import logging, re

logger = logging.getLogger("session logger")


class MemberParser(BaseParser):
    def __init__(self, item, storage):
        """
        {
            "name": "Mauro Sirotnjak",
            "party": "Nova ljevica",
            "committee": 
                [
                    "predsjednik Odbora za prostorno uređenje", 
                    "član Odbora za kontrolu"
                ]
        },
        """
        # call init of parent object
        super(MemberParser, self).__init__(storage)
        logger.info(".:MEMBER PARSER:.")

        person = self.storage.people_storage.get_or_add_object({
            "name": item["name"]
        })

        if item["party"] in ["nestranačka", "Nestranački", "nestranački"]:
            organization = None
        else:
            organization = self.storage.organization_storage.get_or_add_object({
                "name": item["party"],
                "classification": "pg",
            })
            if organization.is_new:
                # TODO fix parladata base api
                # self.storage.organization_membership_storage.get_or_add_object({
                #     "member": organization.id,
                #     "organization": self.storage.main_org_id,
                #     "start_time": None,
                #     "end_time": None,
                #     "mandate": self.storage.mandate_id,
                # })

                self.storage.parladata_api.organizations_memberships.set({
                    "member": organization.id,
                    "organization": self.storage.main_org_id,
                    "start_time": None,
                    "end_time": None,
                    "mandate": self.storage.mandate_id,
                })
                organization.is_new = False

        

        member_data = {
            "member": person.id,
            "role": "member",
            "start_time": None,
            "end_time": None,
            "on_behalf_of": None,
            "mandate": self.storage.mandate_id,
        }
        voter_data = {
            "member": person.id,
            "role": "voter",
            "organization": self.storage.main_org_id,
            "start_time": None,
            "end_time": None,
            "on_behalf_of": None,
            "mandate": self.storage.mandate_id,
        }
        if organization:
            member_data["organization"] = organization.id
            voter_data["on_behalf_of"] = organization.id
            self.storage.membership_storage.get_or_add_object(member_data)

        self.storage.membership_storage.get_or_add_object(voter_data)

        for committee in item["committee"]:
            tokens = committee.split()
            role_str = tokens.pop(0)
            role = self.get_role(role_str)
            name = " ".join(tokens)
            committee = self.storage.organization_storage.get_or_add_object({
                "name": name,
                "classification": "committee",
            })
                
            self.storage.membership_storage.get_or_add_object({
                "member": person.id,
                "role": role,
                "organization": committee.id,
                "start_time": None,
                "end_time": None,
                "on_behalf_of": None,
                "mandate": self.storage.mandate_id,
            })

    def get_role(self, role_str):
        if role_str.startswith("predsjed"):
            return "president"
        elif role_str.startswith("član"):
            return "member"
        else:
            return "member"