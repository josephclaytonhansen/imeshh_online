bl_info = {
    "name": "iMeshh Online",
    "author": "iMeshh Ltd",
    "version": (0, 2, 1),
    "blender": (3, 6, 0),
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

import bpy
import requests
from requests.auth import HTTPBasicAuth

wp_site_url = "https://shopimeshhcom.bigscoots-staging.com"
auth_endpoint = wp_site_url + "/wp-json/wp/v2/users/me"

def authenticated(username, password):
    response = requests.get(auth_endpoint, auth=HTTPBasicAuth(username, password))
    return response.status_code == 200

class AuthPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    username: bpy.props.StringProperty(
        name="Username",
        description="Username",
        default="",
        update=lambda self, context: self.update_auth_status(context)
    )
    password: bpy.props.StringProperty(
        name="Password",
        description="Password",
        default="",
        subtype='PASSWORD',
        update=lambda self, context: self.update_auth_status(context)
    )
    auth_success: bpy.props.BoolProperty(
        name="Authentication Success",
        description="Indicates if the authentication was successful",
        default=False
    )

    def update_auth_status(self, context):
        self.auth_success = False

    def draw(self, context):
        layout = self.layout
        layout.label(text="Enter your iMeshh Online credentials")
        layout.prop(self, "username")
        layout.prop(self, "password")
        layout.operator("imeshh_online.save_credentials", text="Save Credentials").enabled = not self.auth_success

class IMESHH_OT_Authenticate(bpy.types.Operator):
    bl_idname = "imeshh_online.save_credentials"
    bl_label = "Save Credentials"

    def execute(self, context):
        prefs = context.preferences.addons[__name__].preferences
        if authenticated(prefs.username, prefs.password):
            prefs.auth_success = True
            self.report({'INFO'}, "Authentication successful")
        else:
            prefs.auth_success = False
            self.report({'ERROR'}, "Authentication failed")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(AuthPreferences)
    bpy.utils.register_class(IMESHH_OT_Authenticate)

def unregister():
    bpy.utils.unregister_class(AuthPreferences)
    bpy.utils.unregister_class(IMESHH_OT_Authenticate)

if __name__ == "__main__":
    register()