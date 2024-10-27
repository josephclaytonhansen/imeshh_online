bl_info = {
    "name": "imeshh_online",
    "author": "iMeshh Ltd",
    "version": (0, 3, 3),
    "blender": (3, 6, 0),
    "category": "Asset Manager",
    "location": "View3D > Tools > iMeshh Online",
}

from . import manager
from . import operators
from . import ui


from bpy.props import StringProperty
from bpy.types import Operator, AddonPreferences
import requests
from typing import List

import bpy
import requests
from bpy.props import (
    CollectionProperty,
    StringProperty,
    IntProperty,
    BoolProperty,
)
from bpy.types import Panel

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
    bl_idname = "imeshh_online"

    # Existing properties
    username: StringProperty(name="Username", default="")
    password: StringProperty(name="Password", subtype='PASSWORD', default="")
    access_token: StringProperty(name="Access Token", default="", options={'HIDDEN'})
    show_asset_name: BoolProperty(name="Show Asset Names in Browser", default=True)

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
        layout.prop(self, "default_folder")
        layout.prop(self, "show_asset_name")
        layout.operator("imeshh_online.authenticate", text="Authenticate", icon='KEY_HLT')


def register():
    manager.register()
    operators.register()
    ui.register()
    
    bpy.utils.register_class(AuthPreferences)
    bpy.utils.register_class(IMESHH_OT_Authenticate)
    


def unregister():
    ui.unregister()
    operators.unregister()
    manager.unregister()
    
    bpy.utils.unregister_class(IMESHH_OT_Authenticate)
    bpy.utils.unregister_class(AuthPreferences)

if __name__ == "__main__":
    register()