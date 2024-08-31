# Copyright (C) 2024 Aditia A. Pratama | aditia.ap@gmail.com
#
# This file is part of imeshh_online.
#
# imeshh_online is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# imeshh_online is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with imeshh_online.  If not, see <http://www.gnu.org/licenses/>.
import bpy
import pickle
import json
import os
from bpy.types import Operator, WindowManager
from bpy.utils import user_resource, register_class, unregister_class
from bpy.props import StringProperty
from webbrowser import open_new_tab
from . import dependencies

dependencies.preload_modules()

from requests_oauthlib import OAuth1Session  # type: ignore

client_key = "r4ax2NcCOWRr"
client_secret = "uzjzyb1LZLxsE4F0nwgOZGX4dKfMS2ShKBMGEG6LofkhSlSX"
wp_site_url = "https://shopimeshhcom.bigscoots-staging.com"
request_token_url = wp_site_url + "/oauth1/request"
authenticate_url = wp_site_url + "/oauth1/authorize"
access_token_url = wp_site_url + "/oauth1/access"
addon_name = __package__


def get_access(url):
    token_json = os.path.join(get_addon_dir(), "token.json")
    with open(token_json, "r") as file:
        json_data = json.load(file)
        resource_owner_key = json_data.get("oauth_token")
        resource_owner_secret = json_data.get("oauth_token_secret")

    oauth = OAuth1Session(
        client_key,
        client_secret=client_secret,
        resource_owner_key=resource_owner_key,
        resource_owner_secret=resource_owner_secret,
    )

    return oauth.get(url)


def get_addon_dir():
    global addon_name
    user_resources = user_resource("SCRIPTS")
    return os.path.join(user_resources, "addons", addon_name)


def auth_file_exists():
    auth_json = os.path.join(get_addon_dir(), "auth.json")
    token_json = os.path.join(get_addon_dir(), "token.json")
    return os.path.exists(auth_json) and os.path.exists(token_json)


def set_verifier(self, context):
    do_set_verifier(context)


def do_set_verifier(context):
    # update verifier
    wm = context.window_manager
    auth_json = os.path.join(get_addon_dir(), "auth.json")
    with open(auth_json, "r+") as file:
        auth_data = json.load(file)
        auth_data[2] = wm.imeshh_verifier
        file.seek(0)
        json.dump(auth_data, file, indent=4)


class IMESHH_OT_initiate_token(Operator):
    """This will initiate the token\n
    if the verifier in the key file is not found"""

    bl_idname = "imeshh.auth_initiate_token"
    bl_label = "Authenticate"
    bl_description = "Imeshh Authenticate"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return not auth_file_exists()

    def invoke(self, context, event):
        wm = bpy.context.window_manager
        oauth = OAuth1Session(client_key, client_secret=client_secret)
        temp_auth_data = oauth.fetch_request_token(request_token_url)
        authorization_url = oauth.authorization_url(authenticate_url)
        open_new_tab(authorization_url)
        auth_data = (
            temp_auth_data.get("oauth_token"),
            temp_auth_data.get("oauth_token_secret"),
            wm.imeshh_verifier,
        )
        auth_json = os.path.join(get_addon_dir(), "auth.json")
        with open(auth_json, "w") as file:
            json.dump(auth_data, file, indent=4)
        return context.window_manager.invoke_props_dialog(self, width=240)

    def execute(self, context):
        auth_json = os.path.join(get_addon_dir(), "auth.json")
        with open(auth_json, "r") as file:
            json_data = json.load(file)
            resource_owner_key = json_data[0]
            resource_owner_secret = json_data[1]
            verifier = json_data[2]

        oauth = OAuth1Session(
            client_key,
            client_secret=client_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        token_data = oauth.fetch_access_token(access_token_url)
        token_json = os.path.join(get_addon_dir(), "token.json")
        with open(token_json, "w") as file:
            json.dump(token_data, file, indent=4)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Enter Verifier Code from Website")
        wm = bpy.context.window_manager
        layout.prop(wm, "imeshh_verifier", text="")


registry = [
    IMESHH_OT_initiate_token,
]


def register():
    WindowManager.imeshh_verifier = StringProperty(
        name="Verifier Code", update=set_verifier
    )


def unregister():
    del WindowManager.imeshh_verifier
