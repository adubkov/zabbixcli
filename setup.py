from setuptools import setup, find_packages

setup(name='zabbixcli',
      version = '1.0.2',
      description = 'Tool for manage zabbix templates as YAML files.',
      author = 'Alexey Dubkov',
      author_email = 'alexey.dubkov@gmail.com',
      packages = find_packages(),
      scripts = ['zabbixcli','zabbixcli-worker'],
      install_requires = ["argparse", "py-zabbix>=0.5.6"],
      url = 'https://github.com/blacked/zabbixcli',
     )
