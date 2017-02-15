ISIC Archive |build-status| |license-badge|
===========================================
International Skin Imaging Collaboration: Melanoma Project
----------------------------------------------------------

Slides from the SciPy 2015 presentation `are available <https://docs.google.com/presentation/d/1GQJjmSveZMucN1f0Ft4nZQOY0i98d2xhTGLgQreG4jU/edit?usp=sharing>`_.

Development Environment Installation
------------------------------------
Prerequisites
~~~~~~~~~~~~~
* Linux or OSX (Windows host development is possible, but requires additional
  setup steps)

* Git

* Vagrant_ (version >= 1.8.3 recommended)

   **Warning**:
   If Vagrant < 1.8.3 is used, then Ansible_ version > 2.0 must also be installed on the
   host development machine.

* VirtualBox_ (this may sometimes be installed automatically by Vagrant)

Installation
~~~~~~~~~~~~
* Clone the repository:
  ::

    # from within your preferred source development directory
    git clone https://github.com/ImageMarkup/isic-archive.git
    cd isic-archive
    git submodule update --init


* Launch and automatically provision the development VM:
  ::

    # from within the "isic-archive" sub-directory
    vagrant up

Setup
~~~~~
* Use a web browser to visit ``http://127.0.0.1:8080/`` from your host
  development machine.

* Register a new user (this will be an admin user).

* Go to ``Admin console`` -> ``Plugins`` and enable the ``ISIC Archive`` plugin
  (and optionally the ``OAuth2 login`` plugin), then use the button at the top
  of the page to restart the server.

* Visit ``http://127.0.0.1:8080/girder`` in your web browser, as this is where
  the Girder administrative interface is exposed when the plugin is enabled.

* Go to ``Admin console`` -> ``Plugins`` and open the configuration page (gear
  icon) for ``Remote worker``. Set the value
  ``mongodb://localhost:27017/girder_worker`` for both ``Celery broker URL``
  and ``Celery backend URL``, and ``Save``.

* Go to ``Admin console`` -> ``Assetstores`` ->
  ``Create new Filesystem assetstore``, enter ``default`` as the
  ``Assetstore name``, ``/home/vagrant/assetstores/default`` as the
  ``Root directory``, then click ``Create``.

Usage
~~~~~
  **Note**:
  Optionally, after adding the following line to your host systems's
  ``/etc/hosts`` file:
  ::

    127.0.0.1 isic-archive.upstream

  you can visit ``http://isic-archive.upstream:8080/`` on your host development
  machine to access a version of the site that uses the local instance for all
  static front-end code, but proxies all API calls to the instance at
  ``isic-archive.com``.

* To rebuild the front-end code after development changes:
  ::

    # from within the "isic-archive" sub-directory
    vagrant ssh
    cd ~/girder
    npm install --production

* To automatically rebuild the front-end code as changed client files are saved,
  start and leave running:
  ::

    # from within the "isic-archive" sub-directory
    vagrant ssh
    cd ~/girder
    ./node_modules/.bin/grunt watch

* To restart the Girder server after changed server files are saved:
  ::

    # from within the "isic-archive" sub-directory
    vagrant ssh
    sudo supervisorctl restart girder

* To inspect various logs:
  ::

    # Girder's console output
    tail -F /tmp/girder.std*

    # Mongodb's console output
    tail -F /var/log/mongodb/mongod.log

.. |build-status| image:: https://travis-ci.org/ImageMarkup/isic-archive.svg?branch=master
    :target: https://travis-ci.org/ImageMarkup/isic-archive
    :alt: Build Status

.. |license-badge| image:: https://img.shields.io/github/license/ImageMarkup/isic-archive.svg
    :target: https://raw.githubusercontent.com/ImageMarkup/isic-archive/master/LICENSE
    :alt: License

.. _Vagrant: https://www.vagrantup.com/downloads.html

.. _Ansible: https://docs.ansible.com/ansible/intro_installation.html

.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
