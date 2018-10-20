ISIC Archive |build-status| |coverage-badge| |license-badge|
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

* vagrant-hostsupdater_

* VirtualBox_ (this may sometimes be installed automatically by Vagrant)

Installation
~~~~~~~~~~~~
* Clone the repository:
  ::

    # from within your preferred source development directory
    git clone https://github.com/ImageMarkup/isic-archive.git
    cd isic-archive

* Launch and automatically provision the development VM:
  ::

    # from within the "isic-archive" sub-directory
    vagrant up

* Use a web browser to visit ``http://isic-archive.test/`` from your host
  development machine.

* Login as the user ``admin`` with password ``password``. This user can be also used for granting
  additional access permissions to subsequent new users. This user may be deleted once another site
  admin user is created.

Development
~~~~~~~~~~~
  **Note**:
  You can visit ``http://proxy.isic-archive.test/`` on your host development
  machine to access a version of the site that uses the local instance for all
  static front-end code, but proxies all API calls to the instance at
  ``isic-archive.com``.

* To rebuild the front-end code after development changes:
  ::

    # from within the "isic-archive" sub-directory
    vagrant ssh
    ~/env/bin/girder-install web

* To automatically rebuild the front-end code as changed client files are saved,
  start and leave running:
  ::

    # from within the "isic-archive" sub-directory
    vagrant ssh
    ~/env/bin/girder-install web --watch-plugin isic_archive --plugin-prefix app

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

.. |build-status| image:: https://img.shields.io/circleci/project/github/ImageMarkup/isic-archive/master.svg
    :target: https://circleci.com/gh/ImageMarkup/isic-archive
    :alt: Build Status

.. |coverage-badge| image:: https://codecov.io/gh/ImageMarkup/isic-archive/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ImageMarkup/isic-archive
    :alt: Code Coverage

.. |license-badge| image:: https://img.shields.io/github/license/ImageMarkup/isic-archive.svg
    :target: https://raw.githubusercontent.com/ImageMarkup/isic-archive/master/LICENSE
    :alt: License

.. _Vagrant: https://www.vagrantup.com/downloads.html

.. _vagrant-hostsupdater: https://github.com/cogitatio/vagrant-hostsupdater#installation

.. _Ansible: https://docs.ansible.com/ansible/intro_installation.html

.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
