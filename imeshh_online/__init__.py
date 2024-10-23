bl_info = {
    "name": "iMeshh Online",
    "author": "iMeshh Ltd",
    "version": (0, 1, 3),
    "blender": (3, 3, 0),
    "category": "Asset Manager",
    "location": "View3D > Tools > iMeshh Online",
}

addon_version = ".".join(str(x) for x in bl_info["version"])
print("\n")
print("_____________________________________")
print("|                                    |")
print(f"| iMeshh Online version {addon_version} |")
print("| Thank you for using our software   |")
print("|____________________________________|")
print("\n")

import importlib
from . import ops, props, ui
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty
from bpy.types import Operator, AddonPreferences
import requests
from typing import List

import bpy
import requests
import os
import threading
import urllib.parse
from bpy.utils import previews
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
    BoolProperty,
)
from bpy.types import Panel

modules = [
    props,
    ops,
    ui,
]

# Configuration
wp_site_url = 'https://shopimeshhcom.bigscoots-staging.com'
token_endpoint = wp_site_url + "/wp-json/jwt-auth/v1/token"
products_endpoint = wp_site_url + "/wp-json/wc/v3/products"

# Authentication operator (from new_init)
class IMESHH_OT_Authenticate(Operator):
    bl_idname = "imeshh_online.authenticate"
    bl_label = "Authenticate"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        payload = {'username': prefs.username, 'password': prefs.password}
        
        try:
            response = requests.post(token_endpoint, data=payload)
            if response.status_code == 200:
                data = response.json()
                prefs.access_token = data['token']
                print("Authentication successful! Token saved.")
            else:
                print(f"Failed to authenticate. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error during authentication: {e}")

        return {'FINISHED'}


# Preferences for storing credentials and access token (from new_init)
class AuthPreferences(AddonPreferences):
    bl_idname = __name__

    # Existing properties
    username: StringProperty(name="Username", default="")
    password: StringProperty(name="Password", subtype='PASSWORD', default="")
    access_token: StringProperty(name="Access Token", default="", options={'HIDDEN'})
    
    # Missing properties added
    scale_ui_popup: IntProperty(
        name="UI Scale Popup",
        description="Adjust scale of UI popup",
        default=5,
        min=1,
        max=10
    )

    default_folder: StringProperty(
        name="Default Folder",
        description="Folder where assets are downloaded",
        subtype='DIR_PATH',
        default=""
    )

    paths: CollectionProperty(
        name="Asset Paths",
        description="Paths for different asset types",
        type=bpy.types.PropertyGroup  # Adjust if you have a specific PropertyGroup
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "username")
        layout.prop(self, "password")
        layout.prop(self, "default_folder")  # Adding this to the UI
        layout.prop(self, "scale_ui_popup")  # Adding this to the UI
        layout.operator("imeshh_online.authenticate", text="Authenticate", icon='KEY_HLT')



# The classes to register
def register_unregister_modules(modules: List, register: bool):
    """Recursively register or unregister modules by looking for either
    un/register() functions or lists named `registry` which should be a list of
    registerable classes.
    """
    register_func = register_class if register else unregister_class

    for m in modules:
        if register:
            importlib.reload(m)
        if hasattr(m, "registry"):
            for c in m.registry:
                try:
                    register_func(c)
                except Exception as e:
                    un = "un" if not register else ""
                    print(f"Warning: Failed to {un}register class: {c.__name__}")
                    print(e)

        if hasattr(m, "modules"):
            register_unregister_modules(m.modules, register)

        if register and hasattr(m, "register"):
            m.register()
        elif hasattr(m, "unregister"):
            m.unregister()


def register():
    # Register the original modules
    register_unregister_modules(modules, True)

    # Register authentication operator and preferences
    bpy.utils.register_class(IMESHH_OT_Authenticate)
    bpy.utils.register_class(AuthPreferences)


def unregister():
    # Unregister the original modules
    register_unregister_modules(modules, False)

    # Remove the custom property from the scene
    del bpy.types.Scene.imeshh_am

    # Unregister authentication operator and preferences
    bpy.utils.unregister_class(IMESHH_OT_Authenticate)
    bpy.utils.unregister_class(AuthPreferences)
