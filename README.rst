thoth-analyzer
--------------

A library with common functionality for Thoth's analyzers run in OpenShift.

The library provides common functionality for analyzers. It is supposed to be
a base for implementing any new analyzer in the Thoth project.

Currently, there are implemented two core components:

1. A `Command` class for running and executing any external executables.
2. Gathering metadata about the environment where the analyzer was run with all the information such as Python version, arguments supplied to analyzer and others.

Installation
============

This package is realased on PyPI as `thoth-storages
<https://pypi.org/project/thoth-analyzer>`_. Thus you can install this
package using pip or pipenv:

.. code-block:: console

  pipenv install thoth-analyzer
