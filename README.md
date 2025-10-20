# Netbox Backup Plugin

NetBox plugin for Device Backup Integrations.

* Free software: Apache-2.0

> Note that while the goal of this plugin is to support various network device backup
> solutions.  Currently, only Unimus is supported.


> Additionally, note that this plugin uses deprecated `setup.py`. Future versions will 
> address this issue.
> 
## Features

* Render latest device backup to the Netbox Device Page
* Optional backup search/filter Tool

## Compatibility

| NetBox Version | Plugin Version |
|----------------|----------------|
|   >= 4.1.0     | 1.0            |

## Installation

```no-highlight
$ source /opt/netbox/venv/bin/activate
(venv) pip install --force-reinstall git+https://github.com/blynn-dn/backup-plugin
```

### Enable the Plugin

Enable the plugin in `/opt/netbox/netbox/netbox/configuration.py`,
 or if you use netbox-docker, your `/configuration/plugins.py` file :

```no-highlight
PLUGINS = [
    'backup_plugin'
]
```

### Configure Plugin

Configure the plugin in `configuration.py` under the `PLUGINS_CONFIG` parameter.

```no-highlight
PLUGINS_CONFIG = {
    'backup_plugin': {
        'unimus': {
            'base_url': 'https://<FQDN | IP>(:PORT)>/api/v2/',
            'token': '*****',
        }, 
        'ignored_device_roles': []
    }
}
```
Configuration Properties:
* `unimus`: required Unimus parameters
  * `base_url`: Base Unimus API URL
  * `token`: Unimus API Token
* `ignored_device_roles`: A list of devices roles to ignore. The Device Tab `Latest Backup` is not rendered for Devices with these roles. 

### Run Database Migrations

Run the provided schema migrations:

```no-highlight
(venv) $ cd /opt/netbox/netbox/
(venv) $ python3 manage.py migrate
```

### Collect Static Files

Ensure the static files are copied to the static root directory with the `collectstatic` management command:

```no-highlight
(venv) $ cd /opt/netbox/netbox/
(venv) $ python3 manage.py collectstatic
```

### Add Python requirements

Ensure the following python packages are included in /opt/netbox/local_requirements.txt

```no-highlight
backup-plugin @ git+https://github.com/blynn-dn/backup-plugin@main
```
### Restart WSGI Service

Restart the WSGI service to load the new plugin:

```no-highlight
# sudo systemctl restart netbox
```

## Backup Filter/Search Tool
The Backup Filter/Search Tool provides a NetBox page for searching and filtering
Device Backups.

This Feature requires populating a db table with backup data.  This
data includes the following:
* Name of the device
* Optional FK to a Netbox Device 
* Backup Diff info
* An HTML 

## Daily Processing
This plugin was designed with the idea in mind of retrieving a list of
devices from Unimus that contain backups with diffs.  Unimus exposes an 
API for this. (see [Diff - get devices with different backups](https://wiki.unimus.net/display/UNPUB/Full+API+v.2+documentation#FullAPIv.2documentation-Diff-getdeviceswithdifferentbackups)).

Once a list of devices containing backups with a diff are retrieved, each device
is processed to retrieve the last two backups.  The last backups are used to generate
a diff.  The diff in turn, is passed to [Diff2Html](https://diff2html.xyz/) via nodejs. The results
are stored in the backup table.

For more details on how to install Diff2Html and node.js, reference [device_backups.md](docs/device_backups.md)


