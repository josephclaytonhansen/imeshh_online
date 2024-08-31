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
from . import ops, props, auth, ui, prefs
from bpy.utils import register_class, unregister_class
from bpy import context
from typing import List


modules = [
    auth,
    props,
    prefs,
    ops,
    ui,
]


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
    register_unregister_modules(modules, True)
    prefs.load_prefs_json()


def unregister():
    register_unregister_modules(modules, False)
