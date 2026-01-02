#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, téïcée (www.teicee.com)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule, missing_required_lib

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


def _get_service_account(grafana_url, admin_name, admin_password, svc_name):
    get_svc_account_url = grafana_url + "/api/serviceaccounts/search"
    params = {"query": svc_name, "perpage": 1, "page": 1}
    accounts = []

    def get_with_pagination(page):
        params["page"] = page
        result = requests.get(
            get_svc_account_url, auth=(admin_name, admin_password), params=params
        )
        return result

    res = get_with_pagination(1)
    if res.status_code != 200:
        return None

    res_json = res.json()
    accounts.extend(res_json.get("serviceAccounts", []))
    total_count = res_json.get("totalCount", 0)  # Total number of service accounts
    current_page = res_json.get("page", 1)
    per_page = res_json.get("perPage", 10)
    total_pages = (total_count + per_page - 1) // per_page
    while current_page < total_pages:
        current_page += 1
        res = get_with_pagination(current_page)
        if res.status_code != 200:
            break
        res_json = res.json()
        accounts.extend(res_json.get("serviceAccounts", []))

    return accounts


def get_service_account(grafana_url, admin_name, admin_password, svc_name, page=0):
    get_svc_account_url = (
        grafana_url + "/api/serviceaccounts/search?perpage=10&page=1&query="
    )

    # check if user exists by login provided login
    result = requests.get(
        f"{get_svc_account_url}{svc_name}",
        auth=(admin_name, admin_password),
    )

    if result.status_code == 404:
        return None

    return result.json()


def present_svc_account(module):

    if module.params["grafana_url"][-1] == "/":
        module.params["grafana_url"] = module.params["grafana_url"][:-1]

    body = {
        "login": module.params["login"],
        "password": module.params["password"],
        "email": module.params["email"],
        "name": module.params["name"],
        "OrgId": module.params["orgid"],
    }

    {"name": "grafana", "role": "Viewer", "isDisabled": false}

    svc_account = get_service_account(
        module.params["grafana_url"],
        module.params["admin_name"],
        module.params["admin_password"],
        module.params["login"],
    )

    if svc_account is None:
        api_url = module.params["grafana_url"] + "/api/admin/users"
        result = requests.post(
            api_url,
            json=body,
            auth=requests.auth.HTTPBasicAuth(
                module.params["admin_name"], module.params["admin_password"]
            ),
        )
    else:
        user_id = svc_account["id"]
        api_url = module.params["grafana_url"] + "/api/users"
        result = requests.put(
            f"{api_url}/{user_id}",
            json=body,
            auth=requests.auth.HTTPBasicAuth(
                module.params["admin_name"], module.params["admin_password"]
            ),
        )

    if result.status_code == 200:
        return False, True, result.json()

    return (
        True,
        False,
        {"status": result.status_code, "response": result.json()["message"]},
    )


def absent_svc_account(module):
    if module.params["grafana_url"][-1] == "/":
        module.params["grafana_url"] = module.params["grafana_url"][:-1]

    user = get_service_account(
        module.params["grafana_url"],
        module.params["admin_name"],
        module.params["admin_password"],
        module.params["login"],
        module.params["email"],
    )

    if user is None:
        return False, False, "User does not exist"

    user_id = user["id"]
    api_url = f"{module.params['grafana_url']}/api/admin/users/{user_id}"
    result = requests.delete(
        api_url,
        auth=requests.auth.HTTPBasicAuth(
            module.params["admin_name"], module.params["admin_password"]
        ),
    )

    if result.status_code == 200:
        return False, True, result.json()

    return (
        True,
        False,
        {"status": result.status_code, "response": result.json()["message"]},
    )


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

    choice_map = {
        "present": present_svc_account,
        "absent": absent_svc_account,
    }

    module = AnsibleModule(argument_spec=module_args)

    if not HAS_REQUESTS:
        module.fail_json(msg=missing_required_lib("requests"))

    is_error, has_changed, result = choice_map.get(module.params["state"])(module)

    if not is_error:
        module.exit_json(changed=has_changed, output=result)
    else:
        module.fail_json(msg=result)


if __name__ == "__main__":
    main()
