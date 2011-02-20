.. AdminKit documentation master file, created by
   sphinx-quickstart on Wed Jul  7 10:17:49 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to AdminKit's documentation!
====================================

Contents:

.. toctree::
   :maxdepth: 2

Philosophy
==========

AdminKit is a tool to manage systems' configuration. It automates
system administration tasks. All the configuration descriptions are
stored in a central directory tree. This tree is copied on all the
systems by a mean that is outside AdminKit. You can use a network file
system or a distributed revision control for this purpose. For
example, we use git to manage the versionning and distribution of the
files for our needs.

Configuration
=============

Directory structure
-------------------

The files are usually stored under ``/var/lib/adminkit``.

The main file is ``adminkit.conf``. It describes the roles for each
managed system. It must be at the root of ``/var/lib/adminkit``.

The roles are described in the ``roles`` sub-directory. The roles
describe the needed config files and services.

The config files are under the ``files`` sub-directory. You can
specialize the config files by adding the name of the system or any
roles or domain.

adminkit.conf
-------------

``adminkit.conf`` is the entry point of the configuration for your set
of systems administrated under AdminKit. It describes globally what
roles are defined for your systems.

``define_domain(<name>)``
  define the domain name for the hosts used bellow this declaration.

``add_roles(<host>, <name1>, ...)``
  adds roles for ``<host>``.

``add_var(<host>, <name>, <value>)``
  define a variable for ``<host>``.

``add_to_list(<host>, <name>, <value>)``
  add a ``<value>`` to the list ``<name>`` for ``<host>``.

``get_var(<name>)``
  return the value of variable ``<name>``.

The ``adminkit.conf`` file is in fact a python file so you can use any
python construct.

Roles
-----

Roles are defined by files of the same name declared in the
``adminkit.conf`` file. They are located under the ``roles``
directory. Role files can use the following directives:

``add_files(<file desc>, <file desc> ...)``
  add files from the repository to be copied in the system for this
  role. A ``file desc`` can be a path, a list with a path and a
  permission or a path, a permission, a user and a group.

``files_for_service(<service>, <file1>, <file2>...)`` 
  defines files that are added like the ``add_files directive`` but in
  addition, the service is reloaded if any of the files are copied.

``add_dirs(<dir1>, <dir2> ...)``
  create directories.

``check_service_by_pidfile(<service>)``
  checks if the service is still running else restart it for this
  role.

``check_perms((<file>, <perm>), ...)``
  enforces permissions of files for this role.

``add_var(<name>, <value>)``
  define a variable.

``add_to_list(<name>, <value>)``
  add a ``<value>`` to the list ``<name>``.

``get_var(<name>)``
  return the value of variable ``<name>``.

``run_once(<command>)``
  runs the ``<command>`` only once.

``files_to_command(<command>, <regexp>, ...)``
  when a file matching ``<regexp>`` is modified, run the ``<command>``.

``install_pkg(<pkg1>, <pkg2>...)``
  install packages using the system packaging tool. Only apt-get and urpmi
  are supported so far.

``global_conf(<subdir>)``
  run adminkit using the same config file but using the roles and
  files from ``<subdir>`` for each host in the config file. This is
  useful to work on the whole config at once.

In fact role files are python files so you can use any python
construct you want.

Config files
------------

The config files are in fact templates taht can use variables. Some
variables are automatically defined:

``hostname``
  fully qualified host name.

``domainname``
  domain name without host name.

``shortname``
  host name without domain.

``osname``
  operating system name (i.e. debian).

``sysname``
  operating system type (i.e. linux).

``oscode``
  operating system code name (i.e. lenny).

You can also define variables in the main config file or in the role
files using the ``add_var`` definitions.

Variables are used in the config files using the jinja2 conventions
(for example ``{{ hostname }}``). You can also use variables in the
name of files or directories.

You can have specialized version of the same file by using extensions
taken from variable or role names. For example, if you are using a
file called ``/etc/config`` in your role file, adminkit will lookup
``/etc/config.<shortname>``, ``/etc/config.<hostname>``,
``/etc/config.<osname>``...

Example
-------

Imagine we want to manage a system called host1 under AdminKit. So on
the disk, we have the following directory structure: ::

  /var/lib/adminkit/adminkit.conf
  /var/lib/adminkit/roles/base
  /var/lib/adminkit/files/etc/cron.hourly/base
  /var/lib/adminkit/files/etc/mailname

The ``base`` role defines that a system is under AdminKit control and
so it has a crontab entry that run the adminkit command every hour and
it ensures that the mailname file is always coherent with the host name.

Here is the ``adminkit.conf`` file with the assumption that the fqdn
of host1 is host1.domain.com: ::

  define_domain('domain.com')
  add_roles('host1', 'base')

Then the ``base`` role defines what files are defined for the role: ::

  add_files(('/etc/cron.hourly/base', 0755, 'root', 'root'),
             '/etc/mailname')

The file ``/var/lib/adminkit/files/etc/mailname`` will be copied to
/etc/mailname if there is a difference with the local copy. This file
is interesting as we use a variable that will be expanded during the
copy phase: ::

  {{ hostname }}

Once we have everything setup, we just have to call the ``adminkit``
command that runs the checks and takes the needed actions defined in
``adminkit.conf``.
