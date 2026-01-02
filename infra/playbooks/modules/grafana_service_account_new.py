#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, téïcée (www.teicee.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from typing import TypedDict, Any

DOCUMENTATION = """
---
module: user
author:
  - Bastien ANTOINE
version_added: "0.0.1"
short_description: Manage Service Accounts in Grafana
description:
  - Create, Update and delete Service Accounts using Ansible.
requirements: [ "requests >= 1.0.0" ]
notes:
  - Does not support C(check_mode).
  - Does not support C(Idempotency).
options:
  grafana_url:
    description:
      - URL of the Grafana instance.
    type: str
    required: true
  admin_name:
    description:
      - Grafana admin username
    type: str
    required : true
  admin_password:
    description:
      - Grafana admin password
    type: str
    required : true
  login:source 
    description:
      - Login of the user
    type: str
    required : true
  password:
    description:
      - Password of the user. Should be provided if state=present
    type: str
    required : false
  name:
    description:
      - Name of the user.
    type: str
    required : false
  email:
    description:
      - Email address of the user.
    type: str
    required : false
  state:
    description:
      - State for the Grafana User.
    choices: [ present, absent ]
    default: present
    type: str
"""

EXAMPLES = """
- name: Create/Update a user
  grafana.grafana.user:
    login: "grafana_user"
    password: "{{ lookup('ansible.builtin.password') }}"
    email: "grafana_user@localhost.local
    name: "grafana user"
    grafana_url: "{{ grafana_url }}"
    admin_name: "admin"
    admin_password: "admin"
    state: present

- name: Delete user
  grafana.grafana.user:
    login: "grafana_user"
    grafana_url: "{{ grafana_url }}"
    admin_name: "admin"
    admin_password: "admin"
    state: absent
"""

RETURN = r"""
output:
  description: Dict object containing user information and message.
  returned: On success
  type: dict
  contains:
    id:
      description: The ID for the user.
      returned: on success
      type: int
      sample: 17
    email:
      description: The email for the user.
      returned: on success
      type: str
      sample: grafana_user@localhost.local
    name:
      description: The name for the user.
      returned: on success
      type: str
      sample: grafana user
    login:
      description: The login for the user.
      returned: on success
      type: str
      sample: grafana_user
"""

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


__metaclass__ = type


class GrafanaServiceAccount(TypedDict):
    id: int
    uid: str
    name: str
    login: str
    isDisabled: bool
    role: str


class Process:
    def __init__(self, module: AnsibleModule) -> None:
        self._module = module

    def query_grafana(
        self,
        endpoint: str,
        method: str,
        params: dict[str, str] = {},
        body: dict[str, Any] = {},
        raise_404: bool = True,
    ):
        url = f"{self._module.params['grafana_url']}/api/{endpoint}"
        response = requests.request(
            method,
            url,
            auth=(
                self._module.params["admin_name"],
                self._module.params["admin_password"],
            ),
            params=params,
            json=body,
        )
        if raise_404:
            response.raise_for_status()
        else:
            if response.status_code == 404:
                return None
            response.raise_for_status()
        return response.json()

    def _get_service_account(self, svc_name) -> list[GrafanaServiceAccount]:
        get_svc_account_url = "serviceaccounts/search"
        params = {"query": svc_name, "perpage": 1, "page": 1}
        accounts = []

        def get_with_pagination(page):
            params["page"] = page
            result = self.query_grafana(
                "GET", get_svc_account_url, params, raise_404=False
            )
            return result

        res = get_with_pagination(1)
        if not res or res.status_code != 200:
            return accounts

        res_json = res.json()
        accounts.extend(res_json.get("serviceAccounts", []))
        total_count = res_json.get("totalCount", 0)  # Total number of service accounts
        current_page = res_json.get("page", 1)
        per_page = res_json.get("perPage", 10)
        total_pages = (total_count + per_page - 1) // per_page

        while current_page < total_pages:
            current_page += 1
            res = get_with_pagination(current_page)
            if not res or res.status_code != 200:
                break
            res_json = res.json()
            accounts.extend(res_json.get("serviceAccounts", []))

        return accounts

    def _create_service_account(self, svc_name, role) -> GrafanaServiceAccount:
        create_svc_account_url = "serviceaccounts"
        svc_account: GrafanaServiceAccount = self.query_grafana(
            "POST",
            create_svc_account_url,
            body={"name": svc_name, "role": role, "isDisabled": False},
        )  # type: ignore
        return svc_account

    def _service_account_exists(self, svc_name) -> bool:
        accounts = self._get_service_account(svc_name)
        if accounts:
            return True
        return False

    def ensure_service_account_present(
        self, svc_name, role
    ) -> tuple[bool, GrafanaServiceAccount]:
        changed = False
        accounts = self._get_service_account(svc_name)
        if accounts:
            svc_account = accounts[0]
        else:
            svc_account = self._create_service_account(svc_name, role)
            changed = True
        return changed, svc_account


def main():

    # Grafana admin API is only accessible with basic auth, not token
    # So we shall provide admin name and its password
    module_args = {
        "admin_name": {"type": "str", "required": True},
        "admin_password": {"type": "str", "required": True, "no_log": True},
        "service_account_name": {"type": "str", "required": False},
        "grafana_url": {"type": "str", "required": True},
        "role": {
            "type": "str",
            "required": False,
            "default": "Viewer",
            "choices": ["Viewer", "Editor", "Admin"],
        },
        "state": {
            "type": "str",
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
        },
    }

    module = AnsibleModule(argument_spec=module_args)
    process = Process(module)

    if not HAS_REQUESTS:
        module.fail_json(msg=missing_required_lib("requests"))

    if not is_error:
        module.exit_json(changed=has_changed, output=result)
    else:
        module.fail_json(msg=result)


if __name__ == "__main__":
    main()
