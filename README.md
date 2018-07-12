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

- service for Grafana, that push metric by pushgateway and check it in
  specified grafana datasource
- service for Kubernetes rally plugins

Next scenarios are implemented in *rally-plugins*:

* Grafana:
  - check metric pushed from nova instance by pushgateway
  - check metric pushed locally by pushgateway
* Elasticsearch:
  - check data about created nova instance stored
* Kubernetes:
  - create namespace and namespaced pod and delete it then
  - create namespace and namespaced replication controller and
    delete it then
  - list namespaces
  - create namespace and delete it then
  - create namespace and namespaced pod with emptyDir volume and
    delete it then
  - create namespace and namespaced pod with emptyDir volume, check
    it with check command and delete it then
  - create namespace, create secret and namespaced pod with secret
    volume and delete it then
  - create namespace, create secret and namespaced pod with secret
    volume, check it with check command and delete it then
  - create namespace and namespaced pod with hostPath volume and
    delete it then
  - create namespace and namespaced pod with hostPath volume, check
    it with check command and delete it then
  - create namespace, create PV and PVC, create namespaced pod with
    PVC and delete it then
  - create namespace, create PV and PVC, create namespaced pod with
    PVC, check it with check command and delete it then
  - create namespace, create configMap and namespaced pod with
    configMap volume and delete it then
  - create namespace, create configMap and namespaced pod with
    configMap volume, check it with check command and delete it then
  - create namespace and namespaced replicaset and delete it then
  - create namespace and namespaced replicaset, scale it with number
    of replicas, scale revert and delete replicaset then
  - create namespace and namespaced deployment and delete it then
  - create namespace and namespaced deployment, rollout it with changes and
    delete it then
  - create namespace and namespaced statefulset and delete it then
  - create namespace and namespaced statefulset, scale it with number
    of replicas, scale revert and delete statefulset then

For more details how to run and analyze tests, see `docs\source` directory. 
