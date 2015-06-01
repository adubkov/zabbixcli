from setuptools import setup, find_packages

setup(name='zabbixcli',
      version = '1.0',
      description = 'CLI to manage zabbix server',
      author = 'Alexey Dubkov',
      author_email = 'alexey.dubkov@gmail.com',
      packages = find_packages(),
      scripts = ['zabbixcli','zabbixcli-worker'],
      install_requires = ["argparse", "py-zabbix"],
      url = 'https://github.com/blacked/zabbixcli',
     )
