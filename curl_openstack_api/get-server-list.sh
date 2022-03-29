#!/usr/bin/python3

# replace Nova API endpoint

time curl -s "<Nova API Endpoint>" -H "X-Auth-Token: ${1}"

time curl -g -i -X GET <Nova API Endpoint>/v2.1/servers/detail?all_tenants=True \
  -H "Accept: application/json" \
  -H "OpenStack-API-Version: compute 2.79" \
  -H "User-Agent: python-novaclient" \
  -H "X-OpenStack-Nova-API-Version: 2.79" \
  -H "X-Auth-Token: ${1}"
