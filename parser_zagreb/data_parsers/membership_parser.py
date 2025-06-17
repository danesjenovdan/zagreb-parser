import logging
import re

from .base_parser import BaseParser

logger = logging.getLogger("session logger")


class MembershipParser(BaseParser):
    def __init__(self, item, storage):
        """
        {
            "name": "Ema Culi",
            "organization": "Klub gradskih zastupnika HDZ-DP-HSU",
            "role_text": "članovi/članice:"
        },
        """
        # call init of parent object
        super(MembershipParser, self).__init__(storage)
        logger.info(".:MEMBERship PARSER:.")
        logger.debug(item)

        person = self.storage.people_storage.get_or_add_object({"name": item["name"]})
        print(item.keys())
        role = "member" if item["role"].startswith("član") else "president"

        if item["organization"] in ["nestranačka", "Nestranački", "nestranački"]:
            organization = None
        else:
            organization = self.storage.organization_storage.get_or_add_object(
                {
                    "name": item["organization"],
                    "classification": "pg",
                }
            )
            if organization.is_new:
                # TODO fix parladata base api
                # self.storage.organization_membership_storage.get_or_add_object({
                #     "member": organization.id,
                #     "organization": self.storage.main_org_id,
                #     "start_time": None,
                #     "end_time": None,
                #     "mandate": self.storage.mandate_id,
                # })

                self.storage.parladata_api.organizations_memberships.set(
                    {
                        "member": organization.id,
                        "organization": self.storage.main_org_id,
                        "start_time": "2025-06-10T00:00:00Z",
                        "end_time": None,
                        "mandate": self.storage.mandate_id,
                    }
                )
                organization.is_new = False

        member_data = {
            "member": person.id,
            "role": role,
            "start_time": "2025-06-10T00:00:00Z",
            "end_time": None,
            "on_behalf_of": None,
            "mandate": self.storage.mandate_id,
        }
        voter_data = {
            "member": person.id,
            "role": "voter",
            "organization": self.storage.main_org_id,
            "start_time": "2025-06-10T00:00:00Z",
            "end_time": None,
            "on_behalf_of": None,
            "mandate": self.storage.mandate_id,
        }
        if organization:
            member_data["organization"] = organization.id
            voter_data["on_behalf_of"] = organization.id
            self.storage.membership_storage.get_or_add_object(member_data)

        self.storage.membership_storage.get_or_add_object(voter_data)

    def get_role(self, role_str):
        if role_str.startswith("predsjed"):
            return "president"
        elif role_str.startswith("član"):
            return "member"
        else:
            return "member"
