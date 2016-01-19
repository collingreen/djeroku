## Djeroku - Django + Heroku
Djeroku is a project template for django apps with tools and pre-configured
settings that make it easy to leverage the power of heroku. Out of the box
you get a working local development environment and two matching heroku
applications, plus all the tools to easily deploy between them.


### Prerequisites
Djeroku requires pip, virtualenv, and git. Install them however makes
sense on your system (brew, apt-get, etc).


### Creating a new Djeroku Project
Copy the [create_djeroku_project.py](https://raw.githubusercontent.com/collingreen/djeroku/master/create_djeroku_project.py) file from github. This is the only thing
you will initially need to start creating djeroku projects.

`python create_djeroku_project.py project_name`

This will create a new project for you, install all of the requirements,
and leave you with some instructions and tools for what you can do next.


#### Provisioning your Staging and Production heroku apps
Djeroku projects have a djeroku.py that provides some helpful management
commands, including the automatic creating and setup of your staging and
production apps on heroku.

`python djeroku.py heroku_setup`


#### Other Djeroku Commands
You can see all the commands available via djeroku.py by running:
`python djeroku.py --help`


#### Creating a new app
Django projects generate content via a collection of apps. In djeroku, the
expectation is that your project-specific apps are in the
<project_name>/project/apps folder.

From the top level folder of your project, you can create a new app in the apps
folder using the django-admin startapp command as follows:
~~~
mkdir project/apps/new_app_name
django-admin.py startapp new_app_name project/apps/new_app_name
~~~

Obviously this is just convention - if you don't like it, do something
else.

Djeroku sets the project/apps folder as the base directory so you can import
apps in this folder directly without any additional paths.

After creating a new app, you'll need to add it to your django config by
adding its folder in the LOCAL_APPS tuple in settings/common.py and
including any urls in the top level urls.py.


### Djeroku Project Structure
- project_name
  - tools and config for running on heroku
  - project
    - tools and config for the project
    - apps
      - put your apps here


### Djeroku Decisions
Djeroku includes some opinionated decisions about how to structure
a project and what to include by default.

- hosting files are in the top level {project_name} folder
- project config files are in the project folder
- apps live in the `project/apps` folder
- base dir is `project/apps` so apps can be imported directly
- includes `django.contrib.humanize` by default
- includes `django-extensions`
- relies on redis for task queues
- dj-static for hosting static files (use an edge CDN when necessary)


### Staging vs Production
The heroku setup script makes two heroku applications for your project,
staging and production. They are intentionally almost identical, but there
are a couple differences to note:

- staging:
  - DEBUG = True with settings/prod.py
  - ENVIRONMENT_TYPE = 'staging'
  - {project_name}-staging.herokuapp.com

- production
  - DEBUG = False
  - ENVIRONMENT_TYPE = 'production'
  - {project_name}.herokuapp.com


### Additional Tools
Formerly, Djeroku included lib/djeroku and apps/djeroku with some useful tools
for tasks that commonly come up during development (eg, sending html emails from
a template, emailing admins from a template, ssl middleware for heroku,
validating post/get request fields, etc). This has all been moved out of the
project template and onto the github wiki so you can pick and choose what you
want and don't want.


### More Instructions
Check out the [deployment example](https://github.com/collingreen/djeroku/blob/master/deployment_example.md) for more detailed instructions for creating
a new project, adding a new app, and deploying it to both staging and
production.
