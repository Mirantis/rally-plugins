============================
Kubernetes Rally test plugin
============================

Rally plugin for testing kubernetes.

---------------
Getting started
---------------

First of all, you need to create rally env for kubernetes. Use spec from
``samples/platforms/kubespec.yaml`` to create env:

..

  rally env create --name kubernetes --spec samples/platforms/kubespec.yaml

and check it after that:

..

  rally env check

Now, if env is OK, create task config (or use it from
``samples/scenarios/kubernetes/``) and start it:

..

  rally task start samples/scenarios/kubernetes/run-namespaced-pods.yaml

After task is over, you can build report and results for further analyze.

There are next contexts for kubernetes tests:

+------------------------------------+-------------------------------------+----------------------------------------+
| Context                            | Sample                              | Description                            |
+====================================+=====================================+========================================+
| kubernetes.namespaces              | kubernetes.namespaces:              | Creates `count` number of namespaces   |
|                                    |   count: 3                          | and non-default service accounts with  |
|                                    |   with_serviceaccount: yes          | tokens if necessary.                   |
+------------------------------------+-------------------------------------+----------------------------------------+
| kubernetes.replication_controllers | kubernetes.replication_controllers: | Creates `count` number of replication  |
|                                    |   replicas: 1                       | controllers and wait until they won't  |
|                                    |   image: kubernetes/pause           | be ready.                              |
|                                    |   rc_choice_method: round_robin     |                                        |
+------------------------------------+-------------------------------------+----------------------------------------+

There are the following tasks:

+-------------------------------------------------+-----------------------------------------------+
| Task                                            | Description                                   |
+=================================================+===============================================+
| Kubernetes.run_namespaced_pod                   | Creates pod, wait until it won't be running,  |
|                                                 | collect pod's phases info and delete the pod. |
+-------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_delete_replication_controller | Creates rc with number of replicas, wait      |
|                                                 | until it won't be running and delete it.      |
+-------------------------------------------------+-----------------------------------------------+
| Kubernetes.scale_replication_controller         | Scale rc with number of replicas, wait        |
|                                                 | until it won't be running and revert scale it.|
+-------------------------------------------------+-----------------------------------------------+
| Kubernetes.create_delete_namespace              | Creates namespace with random name, wait      |
|                                                 | until it won't be active and then delete it.  |
+-------------------------------------------------+-----------------------------------------------+

Consider each task separately.


Kubernetes.run_namespaced_pod
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| image         | string | image used in pod's manifest        |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/run-namespaced-pods.yaml


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

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-delete-replication-controller.yaml

Kubernetes.scale_replication_controller
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| replicas      | number | number of replicas to scale         |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+

The task supports *constant* type of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/scale-replication-controller.yaml

Kubernetes.create_delete_namespace
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.

To run the test, run next command:

..

  rally task start samples/scenarios/kubernetes/create-delete-namespace.yaml
