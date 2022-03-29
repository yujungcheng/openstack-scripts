#!/bin/bash

# replace the Neutron API endpoint url
# change other header if need to

# sent request to Neutron API with full headers as "openstack" client have.
echo "- curl Neutron API with Accept, User-Agent and X-Auth-Token (no sha256 hashed) headers"
echo "$(date) >>>"
time curl -g -i -X GET "https://<Neutron API Endpoint>/v2.0/networks" \
  -H "Accept: application/json" \
  -H "User-Agent: openstacksdk/0.36.4 keystoneauth1/3.17.3 python-requests/2.20.0 CPython/3.6.8" \
  -H "X-Auth-Token: ${1}"
echo; echo


# sent request to Neutron API with only token header
echo "- curl Neutron API with X-Auth-Token (no sha256 hashed) header only"
echo "$(date) >>>"
time curl -s "https://<Neutron API Endpoint>/v2.0/networks" \
  -H "X-Auth-Token:${1}"
echo; echo



# sent request to Neutron API with only token header which token is hashed 
# this still not work yet.

echo "- curl Neutron API with X-Auth-Token header (sha256 hashed) header only"
echo "$(date) >>>"
token_sha256=$(echo ${1} | sha256hmac | sed 's/  -//g')
echo "sha256hmac: ${token_sha256}"
echo ${token_sha256sum}
#time curl -s "https://<Neutron API Endpoint>/v2.0/networks" \
#    -H "X-Auth-Token: {SHA256}${token_sha256}"
echo curl -s "https://<Neutron API Endpoint>/v2.0/networks" -H "X-Auth-Token: {SHA256}${token_sha256}"
