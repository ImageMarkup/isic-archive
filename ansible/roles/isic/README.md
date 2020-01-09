# isic

An Ansible role to install the ISIC Archive.

## Role Variables

| parameter                 | required | default                            | comments                             |
| --------------------------| -------- | ---------------------------------- | ------------------------------------ |
| `isic_repo_local`         | no       |  `false`                           | Use the local code at `isic_repo_path` (installed as editable), instead of cloning from Git. |
| `isic_env`                | yes      |  -                                 | A mapping of configuration environment variables. |
| `isic_server`             | no       | `false`                            | Enable webserver service. |
| `isic_web`                | no       | `false`                            | Install and build web frontend content. |
| `isic_worker`             | no       | `false`                            | Enable Celery worker service. |
| `girder_bind_public`      | no       | `false`                            | Bind server to all network interfaces. |
| `girder_database_uri`     | no       | `mongodb://localhost:27017/girder` | URL for MongoDB. |
| `girder_development_mode` | no       | `false`                            | Enable Girder's development mode and disable HTTP reverse proxy configuration. |


The following read-only variables are defined after execution of the role:

| variable         | value                 | comments                     |
| ---------------- | --------------------- | ---------------------------- |
| `isic_repo_path` |  `$HOME/isic_archive` | The local path for the repo. |
