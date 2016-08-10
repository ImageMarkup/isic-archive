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
  git submodule init && git submodule update


* Launch and automatically provision the development VM:
::

  # from within the "isic-archive" sub-directory
  vagrant up


* Add the following lines to your host systems's ``/etc/hosts`` file:
::

  172.28.128.100 isic-archive.dev
  172.28.128.100 isic-archive.upstream


Setup
~~~~~
* Use a web browser to visit ``http://isic-archive.dev/`` from your host
  development machine

* Register a new user (this will be an admin user)

* Go to ``Admin console`` -> ``Plugins`` and enable the ``ISIC Archive`` plugin
  (and optionally the ``OAuth2 login`` plugin), then use the button at the top
  of the page to restart the server.

Usage
~~~~~
  **Note**:
  Visit ``http://isic-archive.upstream`` on your host development machine to
  access a version of the site that uses the local instance for all static
  front-end code, but proxies all API calls to the instance at
  ``https://isic-archive.com``.

* To rebuild the front-end code after development changes:
::

  # from within the "isic-archive" sub-directory
  vagrant ssh
  cd isic-archive
  npm install

.. |build-status| image:: https://travis-ci.org/ImageMarkup/isic-archive.svg?branch=master
    :target: https://travis-ci.org/ImageMarkup/isic-archive
    :alt: Build Status

.. |license-badge| image:: https://raw.githubusercontent.com/girder/girder/master/docs/license.png
    :target: https://pypi.python.org/pypi/girder
    :alt: License

.. _Vagrant: https://www.vagrantup.com/downloads.html

.. _Ansible: https://docs.ansible.com/ansible/intro_installation.html

.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
