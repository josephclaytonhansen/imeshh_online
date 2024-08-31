# SPDX-License-Identifier: GPL-3.0-or-later


def preload_modules() -> None:
    """Pre-load the datetime module from a wheel so that the API can find it."""
    import sys

    # if "gazu" in sys.modules:
    #     return

    from . import wheels

    wheels.load_wheel_global("certifi", "certifi")
    wheels.load_wheel_global("charset_normalizer", "charset_normalizer")
    wheels.load_wheel_global("idna", "idna")
    wheels.load_wheel_global("oauthlib", "oauthlib")
    wheels.load_wheel_global("requests_oauthlib", "requests_oauthlib")
    wheels.load_wheel_global("requests", "requests")
    wheels.load_wheel_global("urllib3", "urllib3")
    wheels.load_wheel_global("progress", "progress")
