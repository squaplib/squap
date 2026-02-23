Installation
============

squap depends on:

* Python 3.11+
* PyQtGraph
* PySide6
* numpy

The easiest way to meet these dependencies is with ``pip`` or with a scientific
python distribution like Anaconda.

There are many different ways to install squap, depending on your needs:

pip
---

The most common way to install pyqtgraph is with pip::

    $ pip install squap

conda
-----

? I never use conda ...

From Source
-----------

To get access to the very latest features and bugfixes you have three choices:

1. Clone squap from github::

    $ git clone https://github.com/squaplib/squap
    $ cd install_path/squap

   Now you can install pyqtgraph from the source::

    $ pip install .

2. Directly install from GitHub repo::

    $ pip install git+git://github.com/squap_lib/squap.git@master

   You can change ``master`` of the above command to the branch name or the
   commit you prefer.

3. You can simply place the squap folder someplace importable, such as
   inside the root of another project. squap does not need to be "built" or
   compiled in any way.
