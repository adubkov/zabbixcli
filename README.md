# zabbixcli
This tool allow manipulate on Zabbix objects, like template, over the restful API, keep congituration in YAML files and store them in git.

It current supports the following:
* Templates (with almost full set of objects)
* Hostgroups
* Autoregistration
* Alerts
* Macros

What it's doesn't support yet, but highly desirable:
* It doesn't remove unused items from template. If you remove something from YAML-template, and apply these changes to zabbix, this something, will continue exist in zabbix, and it require manual cleanup
* It doesn't flush zabbix configuration
* No users\groups management yet
* No medias yet

### Requirements
The zabbixcli use [py-zabbix](https://github.com/blacked/py-zabbix) module. Which can be installed with pip.
```bash
pip install py-zabbix
```

# How it works
This tool takes yaml formated template files, resolve dependencies, and make appropriate API calls to zabbix server for create template hierarchy or make another actions.
> **Important:** I highly recommend remove any current templates before use this tool, and manage your zabbix templates only with zabbixcli.

### Templates
Feel free to use any of those templates [zabbixcli-templates](https://github.com/blacked/zabbixcli-templates), modify them or make your own.

### Usage
The tool usage guide can be found by running zabbixcli with `-h` flag
```bash
$ zabbixcli -h

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

#### Configure zabbixcli
First you should configure zabbixcli to works with appropriate zabbix server and use right credentials.
You can either specify these as command arguments, or use environment varible, or mix them.
>**Notice:** Command line arguments have precedence over environment variables.

```yaml
cat >> ~/.bash_profile <<'EOM'
# Cretentials for zabbixcli
export ZBXCLI_USER='admin'
export ZBXCLI_PASS='zabbix'
export ZBXCLI_URL='https://localhost'
EOM
```

#### Apply default template
```yaml
$ cd devops/config/zabbix/templates
$ ls
Template OS Linux

$ zabbixcli -t ./"Template OS Linux"

Syncing : Template OS Linux
 [####################################################################] 56/56
```

#### Delete object from zabbix
You can delete single object from zabbix.
To delete an item from specific template do:
```
$ zabbixcli -D item "Template OS Linux" "Available memory"
```

### Automatic changes apply
Ok, now you know something about zabbixcli, and started store your zabbix config in repo. We all love automation, so it's time to configure automatic changes apply.

You can use [zabbixcli-worker](https://github.com/blacked/zabbixcli/blob/master/zabbixcli-worker) as cronjob to run every minute:

```yaml
$ crontab -e
# Apply changes to zabbix
*/1 * * * * /usr/local/bin/zabbixcli-worker ~/repo/ configs/zabbix/templates/ >> /var/log/zabbixcli-worker 2>&1
```

That's it. Now as soon as you will merge your changes to master, they will applied to zabbix.

>I'd preffer configure `sparce-checkout` in git to pull only folder with templates (because templates folder was part of saltstack states repo in my case).

>I will not detailed describe how to configure sparce-checkout. You can google it.
But basicaly you should add in `~/repo/.git/config`:
```yaml
[core]
    sparcecheckout = true
```
and in `~/repo/.git/info/sparce-checkout` you should add relative path to dir which you only want to pull:
```yaml
configs/zabbix/templates/
```

### Creating first template
This is kind of tutorual will help you create your first template and apply
it to zabbix.

#### Describe a template
First we need to create a directory for our template:
```yaml
$ mkdir "Template MyApp"
$ cd ./"Template MyApp"
```
Then, we need to create init template file.
> Template should be written in yaml format.

When zabbixcli runs it search all `*.yaml` files in this directory, subdirectories and merge them. So you can specify all setting in one huge init.yaml file, or split it to multiple.

```yaml
$ cat >> ./init.yaml <<'EOM'
name: "Template MyApp"  # Name of template in Zabbix
groups:
  - "Templates"         # All templates should be added to Templates group
EOM
```

This will create "Template MyApp" and add it to group "Templates".

#### Describe an applications and items
Lets try to add an item to monitoring:
```yaml
$ mkdir apps
$ cat >> ./apps/myapp.yaml <<'EOM'
applications:
  "MyApp":          # Application name
    - name:         "MyApp service running"     # Item name
      key:          "proc.num[,,,myapp]"        # Item key
      description:  |
                    Monitor if MyApp service running or not.
EOM 
```

As you can see many of parameters were not specified. All of them have predefined values, if you not specify something, that values will be use.

Also you can specify just needed section and pass an other.

#### Describe triggers
```yaml
$ cat >> triggers.yaml <<'EOM'
triggers:
  -                 # Describe trigger
    name:           "MyApp service is not running on {HOST.NAME}"
    warn_level:     "Warning"
    expression:     "{Template MyApp:proc.num[,,,myapp].last(#1)}=0"
EOM
```

#### Apply template to zabbix
Now we have next structure:

```yaml
$ tree ./"Template MyApp"
./Template\ MyApp
├── init.yaml
├── apps
│   └── myapp.yaml
└── triggers.yaml
```

Which will be compile into (yes, you can define all of these in one file):

```yaml
name: "Template MyApp"

groups:
  - "Templates"

applications:
  "MyApp":
    - name:         "MyApp service running"
      key:          "proc.num[,,,myapp]"
      description:  |
                    Monitor if MyApp service running or not.

triggers:
  -
    name:           "MyApp service is not running on {HOST.NAME}"
    warn_level:     "Warning"
    expression:     "{Template MyApp:proc.num[,,,myapp].last(#1)}=0"
```

#### Create a Role
You can aggregate multiple templates into the Role.
>**Notice**: The Role official not implemented in zabbix, so this kind of template aggregation. It will shows under `Roles` hostgroup in templates (That's weird that zabbix mix hostgroups with templates! That's driving me crazy.)

Basically Role is just a template with specific tags and linked templates. So lets create it to see what it is:

```yaml
$ cd ..
$ mkdir "Role MyApp Server"
$ cat >> ./"Role MyApp Server"/init.yaml <<'EOM'
name: "Role MyApp Server"
templates:                # Describe a list of linked templates
  - "Template MyApp"
autoreg:                  # Enable Autoregistration node
  metadata: "my_app_role" # If this metadata is found in zabbix_agent.config
  add_to_group:           # then add discovered host to specifig hostgroup
    - "MyApp Servers"
groups:
  - "Roles"               # Put this role to Roles hostgroup
EOM
```

It will do next:
  - Create template "Role MyApp Server"
  - Create "MyApp Servers" hostgroup
  - Add "Role MyApp Server" to hostgroup "Roles"
  - Link "Template MyApp" to "Role MyApp Server"
  - Create AutoRegistration rule:
    - If metadata field in zabbix_agent.conf on host contain:
      "Role MyApp Server" then add host to "MyApp Servers" group and apply "Role MyApp Server" template on it.

Lets apply it to local zabbix server:
```bash
$ zabbixcli -t ./"Role MyApp Server"
```

#### Alert targeting
You can target alerts from specific Role to specific user or groups.

```yaml
alert:
  do:
  -
    to:             "Email"                     # Media type
    to_group:       "Zabbix administrators"     # Zabbix Group
```

It will create zabbix action with trigger as an event source:
```
Name: Alert for "{role name}" Team

Maintenance status not in maintenance
Template = Role Gateway Server
Trigger value = PROBLEM
Trigger severity >= Warning

Send message to user groups: Zabbix administrators via SMS
```

### Default values
zabbixcli have default values for mostly objects, so no need specify exactly every parameter in template. If it's not specified, it will use default value.
