# Installation #

This document explain how to install and setup Transfr on a Ubuntu Linux for development purpose.

# Dependencies #

  * Django <= 1.0
  * Apache 2
  * MySQL
  * Python 2.5
  * python-yaml
  * python-gettext
  * python-pil

# Downloading #

Transfr haven't been officially released yet, so for now you must perform a checkout or a export on the repository and work with the latest version.

```
svn co http://transfr.googlecode.com/svn/trunk/ transfr
```

# Configuring #

Copy the settings.py.dist file to settings.py and edit it.

Most of configuration have sensible defaults, so you only need to set the bare minimum to get it working;

  * DATABASE\_ENGINE
  * DATABASE\_NAME
  * DATABASE\_USER
  * DATABASE\_PASSWORD
  * DATABASE\_HOST
  * EMAIL\_HOST

But it might be a good idea to also configure these;

  * DEBUG (set to False)
  * ADMINS
  * TIME\_ZONE
  * LANGUAGE\_CODE
  * LANGUAGES


# Setup #

Once your configuration is done you can create the database;

```
python manage.py syncdb
```

Type "yes" when prompted to create a super user, this will be your main admin account.

# You're done #

Now you are ready to run the dev server;

```
python manage.py runserver
```



**Todo**: deploy instructions