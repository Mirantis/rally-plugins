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

+-----------------------+----------------------------+---------------------------------------+
| Context               | Sample                     | Description                           |
+=======================+============================+=======================================+
| kubernetes.namespaces | kubernetes.namespaces:     | Creates `count` number of namespaces  |
|                       |   count: 3                 | and non-default service accounts with |
|                       |   with_serviceaccount: yes | tokens if necessary.                  |
+-----------------------+----------------------------+---------------------------------------+

There are the following tasks:

+--------------------------------+----------------------------+---------------------------------------+
| Task                           | Description                                                        |
+================================+============================+=======================================+
| Kubernetes.run_namespaced_pods | Creates number of pods in sequence, wait them until all won't be   |
|                                | running, collect pods' phases info and delete all pods in sequence.|
+--------------------------------+--------------------------------------------------------------------+

Consider each task separately.

Kubernetes.run_namespaced_pods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task contains next args:

+---------------+--------+-------------------------------------+
| Argument      | Type   | Description                         |
+===============+========+=====================================+
| pods_number   | number | total number of pods in sequence    |
+---------------+--------+-------------------------------------+
| image         | string | image used in pods manifests        |
+---------------+--------+-------------------------------------+
| sleep_time    | number | sleep time between each two retries |
+---------------+--------+-------------------------------------+
| retries_total | number | total number of retries             |
+---------------+--------+-------------------------------------+

The task supports *rps* and *constant* types of scenario runner.
