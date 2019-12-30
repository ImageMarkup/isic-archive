# isic

An Ansible role to install the ISIC Archive.

## Role Variables

| parameter                 | required | default                            | comments                             |
| --------------------------| -------- | ---------------------------------- | ------------------------------------ |
| `isic_repo_version`       | no       |  `master`                          | The version of the repo to checkout. |
| `isic_repo_clone`         | no       |  `true`                            | Clone the repo. |
| `isic_repo_update`        | no       |  `false`                           | Update the repo from its Git remote. |
| `isic_repo_force`         | no       |  `false`                           | Force-checkout the repo. |
| `isic_env`                | yes      |  -                                 | A mapping of configuration environment variables. |
| `isic_server`             | no       | `false`                            | Enable webserver service. |
| `isic_web`                | no       | `false`                            | Install and build web frontend content. |
| `isic_worker`             | no       | `false`                            | Enable Celery worker service. |
| `isic_install_editable`   | no       | `false`                            | Install the Python package in editable mode. |
| `girder_bind_public`      | no       | `false`                            | Bind server to all network interfaces. |
| `girder_database_uri`     | no       | `mongodb://localhost:27017/girder` | URL for MongoDB. |
| `girder_development_mode` | no       | `false`                            | Enable Girder's development mode and disable HTTP reverse proxy configuration. |


The following read-only variables are defined after execution of the role:

| variable         | value                 | comments                     |
| ---------------- | --------------------- | ---------------------------- |
| `isic_repo_path` |  `$HOME/isic_archive` | The local path for the repo. |
