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

* Vagrant_

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

* Use a web browser to visit ``http://isic-archive.test/admin`` from your host
  development machine.

* Login as the user ``admin`` with password ``password``. This user can be also used for granting
  additional access permissions to subsequent new users. This user may be deleted once another site
  admin user is created.

Development
~~~~~~~~~~~
* To rebuild the front-end code after development changes:
  ::

    # from within the "isic-archive" sub-directory
    vagrant ssh
    cd ~/isic_archive/isic-archive-gui
    yarn install
    yarn run build

* To automatically rebuild the front-end code as changed client files are saved,
  start and leave running:
  ::

    yarn run serve

* To proxy all API calls to an external instance during front-end development, run:
  ::

    export PROXY_API_HOST=https://isic-archive.com
    yarn run serve

* To inspect various logs:
  ::

    # Girder's console output
    journalctl -f -u girder

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
