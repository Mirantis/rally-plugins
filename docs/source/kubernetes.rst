============================
Kubernetes Rally test plugin
============================

Rally plugin for testing kubernetes.

---------------
Getting started
---------------

First of all, you need to create rally env for Kubernetes. There are two main
ways to communicate to Kubernetes cluster - specifying auth-token or
certifications. Choose what is suitable for your case and use one of the
following samples.

To create env using certifications, use spec `samples/platforms/kubernetes/cert-spec.yaml`:

```console
rally env create --name kubernetes --spec samples/platforms/kubernetes/cert-spec.yaml
```

For using Kubernetes token authentication, you need to get API key and use
`samples/platforms/kubernetes/apikey-spec.yaml` spec to create env:

```console
rally env create --name kubernetes --spec samples/platforms/kubernetes/apikey-spec.yaml
```

For initialization `Rally environment` to communicate to existing Kubernetes
cluster you can also use system environment variables instead of making
specification json/yaml file. See the list of available options:

* As like regular kubernetes client (kubectl) Rally can read kubeconfig file.
  Call `rally env create --name kubernetes-created --from-sys-env` and Rally
  with check `$HOME/.kube/config` file to the available configuration. Also,
  you can specify `KUBECONFIG` variable with a path different to the default
  `$HOME/.kube/config`.

* Despite the fact that `kubectl` doesn't support specifying Kubernetes
  credentials via separated system environment variables per separate option
  (auth_url, api_key, etc) like other platforms support (OpenStack, Docker,
  etc), Rally team provides this way. Check existing@kubernetes plugin for the
  list of all available variables. Here is a simple example of this feature:

  ```console
  # the URL to the Kubernetes host.
  export KUBERNETES_HOST="https://example.com:3030"
  #  a path to a file containing TLS certificate to use when connecting to the Kubernetes host.
  export KUBERNETES_CERT_AUTH="~/.kube/cert_auth_file"
  # client API key to use as token when connecting to the Kubernetes host.
  export KUBERNETES_API_KEY="foo"
  # client API key prefix to use in token when connecting to the Kubernetes host.
  export KUBERNETES_API_KEY_PREFIX="bar"

  # finally create a Rally environment
  rally env create --name my-kubernetes --from-sysenv
  ```
Check env availbility by the following command:

```console
rally env check
```

Now, if env is OK, create task config (or use it from
``samples/scenarios/kubernetes/``) and start it:

..

  rally task start samples/scenarios/kubernetes/run-namespaced-pods.yaml

After task is over, you can build report and results for further analyze.

There are next contexts for kubernetes tests:

+------------------------------------+-------------------------------------+----------------------------------------+
| Context                            | Sample                              | Description                            |
+====================================+=====================================+========================================+
| namespaces                         | kubernetes.namespaces:              | Creates `count` number of namespaces   |
|                                    |   count: 3                          | and non-default service accounts with  |
|                                    |   with_serviceaccount: yes          | tokens if necessary.                   |
+------------------------------------+-------------------------------------+----------------------------------------+
| kubernetes.namespaces              | kubernetes.namespaces:              | [DEPRECATED!] Creates `count` number   |
|                                    |   count: 3                          | of namespaces and non-default service  |
|                                    |   with_serviceaccount: yes          | accounts with tokens if necessary.     |
+------------------------------------+-------------------------------------+----------------------------------------+
| kubernetes.local_storageclass      | kubernetes.local_storageclass: {}   | Creates local storage class according  |
|                                    |                                     | kubernetes documentation.              |
+------------------------------------+-------------------------------------+----------------------------------------+
| kubernetes.cfg                     | kubernetes.cfg:                     | rally-plugins utility method for       |
|                                    |   sleep_time: 0.5                   | overriding rally kubernetes config     |
|                                    |   retries_total: 100500             | opts.                                  |
|                                    |   prepoll_delay: 1                  |                                        |
+------------------------------------+-------------------------------------+----------------------------------------+

There are the following tasks:

+----------------------------------------------------+-----------------------------------------------+
| Task                                               | Description                                   |
+====================================================+===============================================+
| Kubernetes.create_and_delete_pod                   | Creates pod, wait until it won't be running,  |
|                                                    | collect pod's phases info and delete the pod. |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_delete_replication_controller    | Creates rc with number of replicas, wait      |
|                                                    | until it won't be running and delete it.      |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.scale_replication_controller            | Scale rc with number of replicas, wait        |
|                                                    | until it won't be running and revert scale it.|
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_delete_namespace                 | Creates namespace with random name, wait      |
|                                                    | until it won't be active and then delete it.  |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.list_namespaces                         | List cluster namespaces.                      |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_and_delete_emptydir_volume       | Create pod with emptyDir volume, wait until   |
|                                                    | it won't be running and delete pod then.      |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_check_and_delete_emptydir_volume | Create pod with emptyDir volume, wait until   |
|                                                    | it won't be running, exec pod with check_cmd  |
|                                                    | and delete pod then.                          |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_and_delete_secret_volume         | Create pod with secret volume, wait until     |
|                                                    | it won't be running and delete pod then.      |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_check_and_delete_secret_volume   | Create pod with secret volume, wait until     |
|                                                    | it won't be running, exec pod with check_cmd  |
|                                                    | and delete pod then.                          |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_and_delete_hostpath_volume       | Create pod with hostPath volume, wait until   |
|                                                    | it won't be running and delete pod then.      |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_check_and_delete_hostpath_volume | Create pod with hostPath volume, wait until   |
|                                                    | it won't be running, exec pod with check_cmd  |
|                                                    | and delete pod then.                          |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_and_delete_local_pvc_volume      | Create pv, create pvc, create pod with pvc    |
|                                                    | bound, wait until it won't be running and     |
|                                                    | delete pod, pvc, pv then.                     |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_check_and_delete_local_pvc_volume| Create pv, create pvc, create pod with pvc    |
|                                                    | bound, wait until it won't be running, exec   |
|                                                    | pod with check_cmd; delete pod, pvc, pv then. |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_and_delete_configmap_volume      | Create configMap, create pod with configMap   |
|                                                    | volume, wait until it won't be running and    |
|                                                    | and delete pod then.                          |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_check_and_delete_configmap_volume| Create configMap, create pod with configMap   |
|                                                    | volume, wait until it won't be running, exec  |
|                                                    | pod with check_cmd and delete pod then.       |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_and_delete_replicaset            | Create replicaset with number of replicas,    |
|                                                    | wait for all replicas are ready and delete    |
|                                                    | replicaset then.                              |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_scale_and_delete_replicaset      | Create replicaset with number of replicas,    |
|                                                    | wait for all replicas are ready, scale with   |
|                                                    | scale_replicas, scale revert and delete       |
|                                                    | replicaset then.                              |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_and_delete_deployment            | Create deployment with number of replicas,    |
|                                                    | wait for all replicas are ready and delete    |
|                                                    | deployment then.                              |
+----------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_rollout_and_delete_deployment    | Create deployment with number of replicas,    |
|                                                    | wait for all replicas are ready, rollout with |
|                                                    | some changes and delete deployment then.      |
+----------------------------------------------------+-----------------------------------------------+

Consider each task separately.


Kubernetes.create_and_delete_pod
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| image         | string | image used in pod's manifest        |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-pod.yaml


Kubernetes.create_delete_replication_controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| replicas      | number | number of replicas in RC            |
+---------------+--------+-------------------------------------+
| image         | string | image used in replica's manifests   |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-delete-replication-controller.yaml

Kubernetes.scale_replication_controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+----------------+--------+-------------------------------------+
| Argument       | Type   | Description                         |
+================+========+=====================================+
| replicas       | number | original number of replicas         |
+----------------+--------+-------------------------------------+
| scale_replicas | number | number of replicas to scale         |
+----------------+--------+-------------------------------------+
| image          | number | replication controller image        |
+----------------+--------+-------------------------------------+
| sleep_time     | number | sleep time between each two retries |
+----------------+--------+-------------------------------------+
| retries_total  | number | total number of retries             |
+----------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+

The task supports *constant* and *rps* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/scale-replication-controller.yaml

Kubernetes.create_and_delete_namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-namespace.yaml

Kubernetes.list_namespaces
~~~~~~~~~~~~~~~~~~~~~~~~~~

The task has no args.

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/list-namespaces.yaml

Kubernetes.create_and_delete_emptydir_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| image         | string | image used in pod's manifest        |
+---------------+--------+-------------------------------------+
| mount_path    | string | path to mount volume in pod         |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-emptydir-volume.yaml

Kubernetes.create_check_and_delete_emptydir_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| image         | string | image used in pod's manifest        |
+---------------+--------+-------------------------------------+
| mount_path    | string | path to mount volume in pod         |
+---------------+--------+-------------------------------------+
| check_cmd     | array  | array of strings, which represents  |
|               |        | check command to exec in pod        |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-check-and-delete-emptydir-volume.yaml

Kubernetes.create_and_delete_secret_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| image         | string | image used in pod's manifest        |
+---------------+--------+-------------------------------------+
| mount_path    | string | path to mount volume in pod         |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-secret-volume.yaml

Kubernetes.create_check_and_delete_secret_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| image         | string | image used in pod's manifest        |
+---------------+--------+-------------------------------------+
| mount_path    | string | path to mount volume in pod         |
+---------------+--------+-------------------------------------+
| check_cmd     | array  | array of strings, which represents  |
|               |        | check command to exec in pod        |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-check-and-delete-secret-volume.yaml

Kubernetes.create_and_delete_hostpath_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+----------------------------------------+
| Argument      | Type   | Description                            |
+===============+========+========================================+
| image         | string | image used in pod's manifest           |
+---------------+--------+----------------------------------------+
| mount_path    | string | path to mount volume in pod            |
+---------------+--------+----------------------------------------+
| volume_type   | string | hostPath type according kubernetes api |
+---------------+--------+----------------------------------------+
| volume_path   | string | hostPath path to mount from host       |
+---------------+--------+----------------------------------------+
| sleep_time    | number | sleep time between each two retries    |
+---------------+--------+----------------------------------------+
| retries_total | number | total number of retries                |
+---------------+--------+----------------------------------------+
| command       | array  | array of strings representing          |
|               |        | container command, default is None     |
+---------------+--------+----------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-hostpath-volume.yaml

Kubernetes.create_check_and_delete_hostpath_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+----------------------------------------+
| Argument      | Type   | Description                            |
+===============+========+========================================+
| image         | string | image used in pod's manifest           |
+---------------+--------+----------------------------------------+
| mount_path    | string | path to mount volume in pod            |
+---------------+--------+----------------------------------------+
| volume_type   | string | hostPath type according kubernetes api |
+---------------+--------+----------------------------------------+
| volume_path   | string | hostPath path to mount from host       |
+---------------+--------+----------------------------------------+
| check_cmd     | array  | array of strings, which represents     |
|               |        | check command to exec in pod           |
+---------------+--------+----------------------------------------+
| sleep_time    | number | sleep time between each two retries    |
+---------------+--------+----------------------------------------+
| retries_total | number | total number of retries                |
+---------------+--------+----------------------------------------+
| command       | array  | array of strings representing          |
|               |        | container command, default is None     |
+---------------+--------+----------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-check-and-delete-hostpath-volume.yaml

Kubernetes.create_and_delete_local_pvc_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+-------------------------+--------+-------------------------------------+
| Argument                | Type   | Description                         |
+=========================+========+=====================================+
| persistent_volume       | map    | persistent volume valuable params   |
+-------------------------+--------+-------------------------------------+
| -> size                 | string | PV size in kubernetes size format   |
+-------------------------+--------+-------------------------------------+
| -> volume_mode          | string | Filesystem or Block                 |
+-------------------------+--------+-------------------------------------+
| -> local_path           | string | PV local path to volume on host     |
+-------------------------+--------+-------------------------------------+
| -> access_modes         | list   | PV access modes list of strings     |
+-------------------------+--------+-------------------------------------+
| -> node_affinity        | map    | PV nodeAffinity rule                |
+-------------------------+--------+-------------------------------------+
| persistent_volume_claim | map    | PVC valuable params                 |
+-------------------------+--------+-------------------------------------+
| -> size                 | string | PVC size in kubernetes size format  |
+-------------------------+--------+-------------------------------------+
| -> access_modes         | list   | PVC access modes list of strings    |
+-------------------------+--------+-------------------------------------+
| image                   | string | image used in pod's manifest        |
+-------------------------+--------+-------------------------------------+
| mount_path              | string | path to mount volume in pod         |
+-------------------------+--------+-------------------------------------+
| sleep_time              | number | sleep time between each two retries |
+-------------------------+--------+-------------------------------------+
| retries_total           | number | total number of retries             |
+-------------------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-local-pvc-volume.yaml

Kubernetes.create_check_and_delete_local_pvc_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+-------------------------+--------+-------------------------------------+
| Argument                | Type   | Description                         |
+=========================+========+=====================================+
| persistent_volume       | map    | persistent volume valuable params   |
+-------------------------+--------+-------------------------------------+
| -> size                 | string | PV size in kubernetes size format   |
+-------------------------+--------+-------------------------------------+
| -> volume_mode          | string | Filesystem or Block                 |
+-------------------------+--------+-------------------------------------+
| -> local_path           | string | PV local path to volume on host     |
+-------------------------+--------+-------------------------------------+
| -> access_modes         | list   | PV access modes list of strings     |
+-------------------------+--------+-------------------------------------+
| -> node_affinity        | map    | PV nodeAffinity rule                |
+-------------------------+--------+-------------------------------------+
| persistent_volume_claim | map    | PVC valuable params                 |
+-------------------------+--------+-------------------------------------+
| -> size                 | string | PVC size in kubernetes size format  |
+-------------------------+--------+-------------------------------------+
| -> access_modes         | list   | PVC access modes list of strings    |
+-------------------------+--------+-------------------------------------+
| check_cmd               | array  | array of strings, which represents  |
|                         |        | check command to exec in pod        |
+-------------------------+--------+-------------------------------------+
| image                   | string | image used in pod's manifest        |
+-------------------------+--------+-------------------------------------+
| mount_path              | string | path to mount volume in pod         |
+-------------------------+--------+-------------------------------------+
| sleep_time              | number | sleep time between each two retries |
+-------------------------+--------+-------------------------------------+
| retries_total           | number | total number of retries             |
+-------------------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-check-and-delete-local_pvc-volume.yaml

Kubernetes.create_and_delete_configmap_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+----------------+--------+----------------------------------------+
| Argument       | Type   | Description                            |
+================+========+========================================+
| image          | string | image used in pod's manifest           |
+----------------+--------+----------------------------------------+
| mount_path     | string | path to mount volume in pod            |
+----------------+--------+----------------------------------------+
| configmap_data | map    | configMap resource data                |
+----------------+--------+----------------------------------------+
| subpath        | string | subPath cm data to mount in pod        |
+----------------+--------+----------------------------------------+
| sleep_time     | number | sleep time between each two retries    |
+----------------+--------+----------------------------------------+
| retries_total  | number | total number of retries                |
+----------------+--------+----------------------------------------+
| command        | array  | array of strings representing          |
|                |        | container command, default is None     |
+----------------+--------+----------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-configmap-volume.yaml

Kubernetes.create_check_and_delete_configmap_volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+----------------+--------+----------------------------------------+
| Argument       | Type   | Description                            |
+================+========+========================================+
| image          | string | image used in pod's manifest           |
+----------------+--------+----------------------------------------+
| mount_path     | string | path to mount volume in pod            |
+----------------+--------+----------------------------------------+
| configmap_data | map    | configMap resource data                |
+----------------+--------+----------------------------------------+
| subpath        | string | subPath cm data to mount in pod        |
+----------------+--------+----------------------------------------+
| sleep_time     | number | sleep time between each two retries    |
+----------------+--------+----------------------------------------+
| retries_total  | number | total number of retries                |
+----------------+--------+----------------------------------------+
| check_cmd      | array  | array of strings, which represents     |
|                |        | check command to exec in pod           |
+----------------+--------+----------------------------------------+
| command        | array  | array of strings representing          |
|                |        | container command, default is None     |
+----------------+--------+----------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-check-and-delete-configmap-volume.yaml

Kubernetes.create_and_delete_replicaset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| replicas      | number | number of replicas in replicaset    |
+---------------+--------+-------------------------------------+
| image         | string | image used in replica's manifests   |
+---------------+--------+-------------------------------------+
| name          | string | replicaset custom name, default is  |
|               |        | random                              |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+
| status_wait   | bool   | wait for status if True             |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-replicaset.yaml

Kubernetes.create_scale_and_delete_replicaset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| replicas      | number | number of replicas in replicaset    |
+---------------+--------+-------------------------------------+
| scale_replicas| number | number of replicas to scale         |
+---------------+--------+-------------------------------------+
| image         | string | image used in replica's manifests   |
+---------------+--------+-------------------------------------+
| name          | string | replicaset custom name, default is  |
|               |        | random                              |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+
| status_wait   | bool   | wait for status if True             |
+---------------+--------+-------------------------------------+

The task supports *constant* and *rps* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-scale-and-delete-replicaset.yaml

Kubernetes.create_and_delete_deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| replicas      | number | number of replicas in deployment    |
+---------------+--------+-------------------------------------+
| image         | string | image used in replica's manifests   |
+---------------+--------+-------------------------------------+
| name          | string | deployment custom name, default is  |
|               |        | random                              |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+
| status_wait   | bool   | wait for status if True             |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-and-delete-deployment.yaml

Kubernetes.create_rollout_and_delete_deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| replicas      | number | number of replicas in deployment    |
+---------------+--------+-------------------------------------+
| env           | array  | array of mappings representing      |
|               |        | kubernetes container's env          |
+---------------+--------+-------------------------------------+
| resources     | map    | map representing container resources|
|               |        | requirements                        |
+---------------+--------+-------------------------------------+
| changes       | map    | map with allowed keys env, resources|
|               |        | or image for rollout deployment     |
+---------------+--------+-------------------------------------+
| image         | string | image used in replica's manifests   |
+---------------+--------+-------------------------------------+
| name          | string | replicaset custom name, default is  |
|               |        | random                              |
+---------------+--------+-------------------------------------+
| command       | array  | array of strings representing       |
|               |        | container command, default is None  |
+---------------+--------+-------------------------------------+
| status_wait   | bool   | wait for status if True             |
+---------------+--------+-------------------------------------+

The task supports *constant* and *rps* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-rollout-and-delete-deployment.yaml
