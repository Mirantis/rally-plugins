# Rally plugins

Rally custom plugins for testing platform components.

## Installation

To add custom rally plugins to rally plugin list, just pip the repo:

```sh
pip install .
```

Then you can check that custom plugins included in rally plugins list:

```sh
rally plugin list | grep <plugin_name>
```

## Uninstall

To uninstall the repo, just pip uninstall it:

```sh
pip uninstall rally-plugins
```

## Dependencies

*rally-plugins* depends on [rally-openstack](https://github.com/openstack/rally-openstack) package.

## Current state

Currently there are next services:

- service for Grafana, that push metric by pushgateway and check it in specified grafana datasource.

Next scenarios are implemented in *rally-plugins*:

- grafana: check metric pushed from nova instance by pushgateway
- grafana: check metric pushed locally by pushgateway
- elasticsearch: check data about created nova instance stored
- kubernetes: create namespace and namespaced pod and delete it then
- kubernetes: create namespace and namespaced replication controller and
  delete it then
- kubernetes: list namespaces
- kubernetes: create namespace and delete it then
- kubernetes: create namespace and namespaced pod with emptyDir volume and
  delete it then
- kubernetes: create namespace and namespaced pod with emptyDir volume, check
  it with check command and delete it then
- kubernetes: create namespace, create secret and namespaced pod with secret
  volume and delete it then
- kubernetes: create namespace, create secret and namespaced pod with secret
  volume, check it with check command and delete it then
  
For more details how to run and analyze tests, see `docs\source` directory. 
