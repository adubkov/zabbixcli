# Zabbix cmdline tool
This tool allows for the manipulation of objects in Zabbix via the restful API.

It current supports the following:
* Create Templates with almost full set of required objects.
* Create Hostgroups and link Templates to them.
* Create Autoregistration Rules.

# How it works
This tool takes yaml formated template file, calculate dependencies, and make required requests to zabbix server for create template hierarchy and other objects if required.
> **Important**: It`s recomended to remove any templates before use this tool.

### Requirements
The zabbix & argparse packages are required but not currently part of the standard library.
```
cd devops/lib           # go to devops repo
pip install zabbix/     # install zabbix module from local repo
pip install argparse
```

### Usage
The tool itself is self documenting, and a helpful usage guide can be found by running the `-h` flag
```
$ zabbixcli

usage: zabbixcli [-h] [-t TEMPLATE] [-s SERVER] [-u USER] [-p PASS] [-o] [-d]
                 [-D DELETE [DELETE...]]

Template based zabbix configuration tool

optional arguments:
  -h, --help                          Show this help message and exit
  -t TEMPLATE,  --template TEMPLATE   Template name for sync
  -s SERVER,    --server SERVER       Zabbix server URL
  -u USER,      --user USER           Zabbix user name
  -p PASS,      --pass PASS           Zabbix user password
  -o, --only                          Sync only specified templates
  -d, --debug                         Enable debug mode
  -D DELETE [DELETE ...], --delete DELETE [DELETE ...]
                                      Delete object from zabbix.
  Example: -D item "Template OS Linux" "Available memory"
                                      
```

## Push default template
```
$ cd devops/config/zabbix/templates
$ ls
Template OS Linux

$ zabbixcli -h=https://zabbix.server -u=user -p=pass -t="Template OS Linux"

Syncing : Template OS Linux
 [####################################################################] 56/56
```

## Delete object from zabbix

You can delete single object from zabbix.

To delete an item from specific template do:
```
$ zabbixcli -D item "Template OS Linux" "Available memory"
```

# Creating first template

## Describe a template
First we need to create a directory for our template:
```bash
$ mkdir "Template MyApp"
$ cd ./"Template MyApp"
```
Then, we need to create init template file.
> Template should be written in yaml format.

When zabbixcli runs it search all *.yaml files in this directory, subdirectories and merge them. So you can specify all setting in one huge init.yaml file, or split it to multiple.

```bash
$ vi ./init.yaml
```

```yaml
name: "Template MyApp"  # Name of template in Zabbix
groups:
  - "Templates"         # All templates should be added to Templates group
```

This will create "Template MyApp" and add it to group "Templates".

## Describe an applications and items
Lets try to add an item to monitoring:
```bash
$ mkdir apps
$ vi ./apps/myapp.yaml
```

```yaml
applications:
  "MyApp":          # Application name
    - name:         "MyApp service running"     # Item name
      key:          "proc.num[,,,myapp]"        # Item key
      description:  |
                    Monitor if MyApp service running or not.
```

As you can see many of parameters were not specified. All of them have predefined values, if you not specify something, that values will be use.

Also you can specify just needed section and pass an other.

## Describe triggers
```bash
$ vi triggers.yaml
```

```yaml
triggers:
  -                 # Describe trigger
    name:           "MyApp service is not running on {HOST.NAME}"
    warn_level:     "Warning"
    expression:     "{Template MyApp:proc.num[,,,myapp].last(#1)}=0"
```

## Push template to zabbix
Now we have next structure:

```bash
$ tree ./"Template MyApp"
./Template\ MyApp
├── init.yaml
├── apps
│   └── myapp.yaml
└── triggers.yaml
```

Which will compile in:

```yaml
name: "Template MyApp"  # Name of template in Zabbix

groups:
  - "Templates"         # All templates should be added to Templates group

applications:
  "MyApp":          # Application name
    - name:         "MyApp service running"     # Item name
      key:          "proc.num[,,,myapp]"        # Item key
      description:  |
                    Monitor if MyApp service running or not.

triggers:
  -                 # Describe trigger
    name:           "MyApp service is not running on {HOST.NAME}"
    warn_level:     "Warning"
    expression:     "{Template MyApp:proc.num[,,,myapp].last(#1)}=0"
```

## Create a Role
You can aggregate multiple templates into the Role.
Role it`s just a template with specific tags. Lets create it:

```bash
$ cd ..
$ mkdir "Role MyApp Server"
$ vi ./"Role MyApp Server"/init.yaml
```

```yaml
name: "Role MyApp Server"
templates:                # Describe a list of linked templates
  - "Template MyApp"
autoreg:                  # Enable Autoregistration node
  metadata: "my_app_role" # If this metadata is found in zabbix_agent.config
  add_to_group:           # then add discovered host to specifig hostgroup
    - "MyApp Servers"
groups:
  - "Roles"               # Put this role to Roles hostgroup
```

This will do next:
  - Create template "Role MyApp Server"
  - Create "MyApp Servers" hostgroup
  - Add "Role MyApp Server" to hostgroup "Roles"
  - Link "Template MyApp" to "Role MyApp Server"
  - Create AutoRegistration rule:
    - If metadata field in zabbix_agent.conf on host contain:
      "Role MyApp Server" then add host to "MyApp Servers" group and apply "Role MyApp Server" template on it.

Lets push it on local zabbix server with default user and pass (`admin`,`zabbix`):
```bash
$ zabbixcli -t="Template MyApp"
```

## Alert targeting
You can target alerts from specific Role to specific user or groups.

```
alert:
  do:
  -
    to:             "Email"                     # Media type
    to_group:       "Zabbix administrators"     # Zabbix Group
```

This will create zabbix action with trigger as an event source:
```
Name: Alert for "{role name}" Team

Maintenance status not in maintenance
Template = Role Gateway Server
Trigger value = PROBLEM
Trigger severity >= Warning

Send message to user groups: Zabbix administrators via SMS
```

## Examples
You can find addition, more complex, examples in `devops/config/zabbix/templates`

# List of default values
```yaml
disabled:     False         # Status of zabbix object.
```
## Discovery
```yaml
delay:        3600          # Delay between discoveries in seconds
lifetime:     30            # How long autodiscovered items will exist in days
```

## Items
```yaml
return_type:  Numeric       # Type of return data
method:       Agent         # Method of checking
interval:     60            # How often items should be checked in seconds
history:      7             # How long values will stored in days
trends:       365           # How long trends values will stored in days
store_as:     'as is'       # How to store values 'as is', 'speed', 'change'
```

## Triggers
```yaml
warn_level:   None          # Level of severity
```

## Graphs
```yaml
height:       200           # Height of graph
width:        900           # Width of graph
type:         Normal        # Type of graph: 'normal', 'stacked', 'pie', 'exploded'
func:         avg           # Function that applies to graph
color:        009900        # Color of metric object
y_side:       left          # Side to shows Y-axis legend
style:        Line          # Style of metric object
gitype:       Simple
3d_view:      0             # 3d view of pie type graph
show_legend:  1             # Show legend under the graph
show_working_time:  0       # Show working time on the graph
show_triggers:      0       # Show triggers values on the graph
y_min_type:   Calculated    # Type of Y min ('fixed', 'calculated', 'item')
y_max_type:   Calculated    # Type of Y max ('fixed', 'calculated', 'item')
percent_right:  0.0
percent_left:   0.0
```

## Alerts
```yaml
recovery:         True,
trigger_status:   'problem',# problem, ok
warn_level:       'warning',# Trigger warn_level
subject:          '[{EVENT.ID}] {TRIGGER.STATUS}: {TRIGGER.NAME} on {HOST.NAME1}',
text:             ("{TRIGGER.SEVERITY}:\n"
                     "{TRIGGER.DESCRIPTION}\n"
                     "{HOST.NAME1}:[{ITEM.NAME1}]: {ITEM.VALUE1}"),
recovery_subject: '[{EVENT.ID}] {TRIGGER.STATUS}: {TRIGGER.NAME} on {HOST.NAME1}',
recovery_text:    ("{TRIGGER.SEVERITY}:\n"
                     "{TRIGGER.DESCRIPTION}\n"
                     "{HOST.NAME1}:[{ITEM.NAME1}]: {ITEM.VALUE1}"),
eventsource:      0,        # Trigger handle
eval:             0,        # AND/OR: 0, AND: 1, OR: 2
escalation_time:  300,      # Must be >60s
to:               'Email',  # Email: 1
action:           'message',# message, [ execute is not supported yet ]
cmp:              '>=',     # =, !=, >=, <=
```
