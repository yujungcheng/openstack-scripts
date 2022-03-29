#!/bin/bash


# update <Username>
# update <Password>
# update <Keystone Puboic Endpoint>, the endpoint should include port number


curl --silent -X POST -H "Content-Type: application/json"   -d '{ "auth": { "identity": { "methods": ["password"], "password": { "user": { "name": "<Username>", "domain": { "id": "default" }, "password": "<Password>" }  } }, "scope": { "project": { "name": "admin", "domain": { "id": "default" } } } } }' -i "https://<Keystone Puboic Endpoint>/v3/auth/tokens" | grep X-Subject-Token | cut -d ":" -f 2 | cut -d' ' -f2


