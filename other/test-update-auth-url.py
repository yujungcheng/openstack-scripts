#!/usr/bin/python3

from os import environ as env


print("Original AUTH URL: %s" % env['OS_AUTH_URL'])

# set version to OS_AUTH_URL if not specified.
if not (env['OS_AUTH_URL'].endswith("/v2.0") or env['OS_AUTH_URL'].endswith("/v3")):
    if env['OS_AUTH_URL'].endswith("/"):
        env['OS_AUTH_URL'] = env['OS_AUTH_URL'][:-1]
    if env['OS_IDENTITY_API_VERSION'] == "3":
        env['OS_AUTH_URL'] += "/v3"
    else:
        env['OS_AUTH_URL'] += "/v2.0"

    print("API Version: %s" % env['OS_IDENTITY_API_VERSION'])
    print("Updaged AUTH URL: %s" % env['OS_AUTH_URL'])

