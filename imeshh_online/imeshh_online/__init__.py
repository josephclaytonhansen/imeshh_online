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
from . import secrets

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

## Configuration
wp_site_url = 'https://shopimeshhcom.bigscoots-staging.com'
token_endpoint = wp_site_url + "/wp-json/jwt-auth/v1/token"
subscriptions_endpoint = wp_site_url + "/wp-json/wc/v1/subscriptions"

env_vars = secrets.get_secrets()
wc_consumer_key = env_vars.get("WC_CONSUMER_KEY")
wc_consumer_secret = env_vars.get("WC_CONSUMER_SECRET")

class AuthPreferences(AddonPreferences):
    bl_idname = "imeshh_online"

    username: StringProperty(name="Username", default="")
    password: StringProperty(name="Password", subtype='PASSWORD', default="")
    access_token: StringProperty(name="Access Token", default="", options={'HIDDEN'})
    subscription_id: IntProperty(name="Subscription ID", default=0, options={'HIDDEN'})  # New hidden property
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
        type=bpy.types.PropertyGroup
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "username")
        layout.prop(self, "password")
        layout.prop(self, "default_folder")
        layout.prop(self, "show_asset_name")
        layout.operator("imeshh_online.authenticate_and_check_subscription", text="Authenticate & Check Subscription", icon='KEY_HLT')


class IMESHH_OT_AuthenticateAndCheckSubscription(Operator):
    bl_idname = "imeshh_online.authenticate_and_check_subscription"
    bl_label = "Authenticate & Check Subscription"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        payload = {'username': prefs.username, 'password': prefs.password}
        
        # Step 1: Authenticate
        try:
            response = requests.post(token_endpoint, data=payload)
            if response.status_code == 200:
                data = response.json()
                prefs.access_token = data['token']
                print("Authentication successful! Token saved.")
            else:
                print(f"Failed to authenticate. Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                return {'CANCELLED'}
        except Exception as e:
            print(f"Error during authentication: {e}")
            return {'CANCELLED'}
        
        headers = {
            "Authorization": f"Bearer {prefs.access_token}",
            "Content-Type": "application/json"
        }

        # Step 2: Get User ID by Email
        try:
            user_info_response = requests.get(
                f"{wp_site_url}/wp-json/wp/v2/users/me",
                headers={'Authorization': f'Bearer {prefs.access_token}'}
            )
            
            if user_info_response.status_code == 200:
                user_data = user_info_response.json()
                prefs.user_id = str(user_data.get('id', ''))
                print(f"User ID retrieved: {prefs.user_id}")
            else:
                print(f"Failed to retrieve user info. Status Code: {user_info_response.status_code}")
                print(f"Response: {user_info_response.text}")
                return {'CANCELLED'}
        
        except Exception as e:
            print(f"Error retrieving user information: {e}")
            return {'CANCELLED'}

        # Step 3: Check subscription
        try:
            subscription_response = requests.get(
                subscriptions_endpoint,
                auth=(wc_consumer_key, wc_consumer_secret),
                headers=headers,
                params={"customer": user_id}  # Use the integer user ID
            )
            
            if subscription_response.status_code == 200:
                subscriptions = subscription_response.json()
                if subscriptions:
                    # Assume the first subscription is the one to use
                    subscription = subscriptions[0]
                    prefs.subscription_id = subscription['id']
                    print(f"Subscription ID {prefs.subscription_id} saved.")
                else:
                    print("No subscriptions found for this user.")
            else:
                print(f"Failed to retrieve subscriptions. Status Code: {subscription_response.status_code}")
                print(f"Response: {subscription_response.text}")
        
        except Exception as e:
            print(f"Error retrieving subscription information: {e}")

        return {'FINISHED'}


def register():
    manager.register()
    operators.register()
    ui.register()
    
    bpy.utils.register_class(AuthPreferences)
    bpy.utils.register_class(IMESHH_OT_AuthenticateAndCheckSubscription)
    


def unregister():
    ui.unregister()
    operators.unregister()
    manager.unregister()
    
    bpy.utils.unregister_class(AuthPreferences)
    bpy.utils.unregister_class(IMESHH_OT_AuthenticateAndCheckSubscription)

if __name__ == "__main__":
    register()