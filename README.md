## OpenStack Scripts
Python3 scripts for querying OpenStack data to provide rich infofor further troubleshooting and data collection.
Tested on Ubuntu 20.04 python3-openstacksdk 0.46.0-0ubuntu1

Include some scripts for CEPH storage.

## Scripts:
```
ops-vm.py    - query instance data
ops-net.py    - query network data
ops-swift.py    - query swift object data
ops-swift-check-object.py    - check object metadata/status
ops-swift-list-container-sync.py    - get container sync json file
ops-swift-check-container-sync.py    - check container sync status
ops-swift-create-container-sync.py    - create / remove container sync
ops-swift-monitor-object-disk.py    - monitor object disk and partions change
ops-cinder-map-rbd-du-with-volume-info.py    - map rbd du output to cinder volume info
ops-client-example.py    - examples use openstack component clients for developing

other/pygrep.py    - comparing specific column/field value between two files
other/db-get-last-vm-action.py    - get instance last start/stop/create action from database
```

## Version
- 2021-07-10 - draft
- 2021-07-17 - update network script

## Install python3 openstacksdk and openstackclient
```
apt install python3-openstacksdk python3-openstackclient
```

## Usage
```
# list projects
$ ./ops-vm.py --project

# list users
$ ./ops-vm.py --user

# list VM
$ ./ops-vm.py --vm <Project ID> 

# show VM
$ ./ops-vm.py <VM ID> [<VM ID> ...]

# list network
$ ./ops-net.py list network <Project ID>

# list router
$ ./ops-net.py list router <Project ID>

# show network
$ ./ops-net.py show network <Network ID>

# show router
$ ./ops-net.py show router <Router ID>

# list swift container
$ ./ops-swift.py list container <Project ID>

# list swift object
$ ./ops-swift.py list object <Project ID> <Container Name>

# show swift container
$ ./ops-swift.py show container <Project ID> <Container Name>

# show swift object
$ ./ops-swift.py show object <Project ID> <Container Name> <Object Name>

# check swift object metadata (multithread)
$ edit ./clouds.yaml for authentication
$ ./ops-swift-check-object.py --cloud <Cloud Name) --projectname <Project Name> --containername <Container Name>
$ ./ops-swift-check-object.py --cloud <Cloud Name) --projectname <Project Name> --containername <Container Name> --objectlistfile <Object List File>>

```

## Todo
* move common functions into common.py
* redesign resume feature for ops-swift-check-object.py, store sequence number when getting object list.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Please make sure to update tests as appropriate.

## License
Apache License 2.0
