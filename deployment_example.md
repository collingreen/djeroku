## A full example of deploying the djeroku site itself


### Download the create_djeroku_project.py script
Download the create_djeroku_project.py script from github:
https://raw.github.com/collingreen/djeroku/master/create_djeroku_project.py


## Creating the Project
`python create_djeroku_project.py djeroku_site`


## Getting a Heroku account and the heroku toolbelt
First, go to heroku.com and download the heroku toolbelt, which includes
the heroku command line interface required for the rest of this to work. You'll
also need to sign up for a heroku account.


## Setting up the staging and production heroku applications
The djeroku.py script in the top project directory has a useful function that
basically handles the entire heroku setup process for you, including creating
two (nearly) identical environments (staging and production), setting everything
up, and provisioning a bunch of free addons for each. You should really have a
look in the file to see what is happening under the hood.  You can easily edit
the addons or environment variables you want set inside the file.

`python djeroku.py heroku_setup`

There are several prompts along the way and it will warn you if something fails.
The most frustrating part of the entire process (assuming it works) is that
django projects require underscores not dashes, and heroku requires dashes
not underscores.

NOTE - the heroku_setup script generates a new SECRET_KEY for your production
app and sets it in the production environment.


## Creating an App
Django projects generate content via a collection of apps. In djeroku, the
expectation is that your project-specific apps are in the
<project_name>/project/apps folder. You can obviously put them wherever you
like, but these examples are based on this layout. Other than that, this section
is just plain django app creation instructions.

You can create a new app using the django-admin startapp command from the
project root:
~~~
mkdir project/apps/djeroku_app
django-admin.py startapp djeroku_app project/apps/djeroku_app
~~~

Now, open `settings/common.py` and add the new djeroku app to the LOCAL_APPS
tuple. Djeroku sets the django BASE_DIR to the apps folder so you don't need to
put any path on the front of your imports.
~~~
LOCAL_APPS = (
    'djeroku_app',
)
~~~

Next, hook up the app urls in the project urls.py by adding this line as the
first item inside the patterns list. This will let the `urls.py` file in
the new djeroku app specify routes that your project can serve.

`url(r'', include('djeroku_app.urls')),`

You'll need to create some views if you want to see anything. You can also
just download the djeroku_app project and place it in the project/apps folder
(plus the LOCAL_APPS and urls.py updates above).


djeroku/views.py
~~~
from django.shortcuts import HttpResponse

def test(request):
    return HttpResponse("Djeroku is great")
~~~

djeroku/urls.py
~~~
from django.conf.urls import url

urlpatterns = [
    url(r'^test/', 'apps.djeroku.views.test')
]
~~~


## Test everything locally
It's time to run the project locally. First, navigate back up to the
djeroku_site folder that holds manage.py

Run the djeroku `serve` command -- this just runs the standard
django migrate, collecstatic, and then runserver commands
`python djeroku.py serve`

Test it by going to 127.0.0.1:8000 and confirming you can see the Djeroku
test content we created above (or whatever view you routed from '/').

TODO: insert screenshot


### Commit it?
Look at all that amazing work we did. Better commit it. The
`python djeroku.py setup_heroku` command earlier created a git repository for
us, so all we need to do is add and commit.

~~~
git add .
git commit -m"initial djeroku template commit"
~~~


## Push to Staging
Now that we have a commit, we can push it to our staging app on heroku. Heroku
uses git pushes for deployment, so you can just call `git push staging master`.
You may also need to run database creation or migration scripts, and you may
need to collect your static assets
(`heroku run python manage.py <commands> --app yourapp-staging`). You can also
just use the djeroku.py script again which wraps all of those up into one
command:

`python djeroku.py deploy staging`

That's it! Heroku will churn away and crunch our commit into a working 'app
slug' and turn our new staging app on.

NOTE: you can tell heroku which app to use by default, but I like to leave
it as explicitly required, so I never accidentally do something on the wrong
app.

When the build completes, you can see the app by going to
djeroku-site-staging.herokuapp.com in a browser.


#### Error! ALLOWED_HOSTS
If you forget to update your ALLOWED_HOSTS setting, your app will constantly
fail while DEBUG is false. Update your settings if this is happening to you.

> NOTE! You may need to prefix your ALLOWED_HOSTS paths with a . to have them
  work in heroku!
  For example: `.djeroku-site-staging.herokuapp.com`



## Deploying to Production
Now that we feel confident that the site is working in staging, we can deploy
to production in exactly the same way as before:
`git push production master`

You can also just call `python djeroku.py deploy production`

Now the production site is up as well, at the production url,
djeroku-site.herokuapp.com.


Now, if this was a public app, I would leave it up (and probably set up a real
domain pointing to it, not just the .herokuapp.com one), but for now I put both
apps into maintenance mode using the heroku command line.  I generally keep my
staging apps in maintenance always, unless I'm actively testing on them.

~~~
heroku maintenance:on --app=djeroku-site-staging
heroku maintenance:on --app=djeroku-site
~~~

A quick check with the browser shows them both in maintenance, safe and sound.


### Filestructure
This is the resulting application structure and a brief explanation of each
file/folder. Your project will end up with a similar structure.

~~~
my-development-folder
|-- djeroku_site
   |-- venv (the virtual environment for this project)
   |-- djeroku_site (the folder containing everything - this will be put in git)
      |-- requirements.txt (heroku will look at this, which leads to the production requirements)
      |-- reqs (holds the requirements files for dev vs production)
         |-- dev.txt (the python packages you need for development)
         |-- prod.txt (the python packages you need for production)
         |-- common.txt (the python packages shared for both dev and production)
      |-- Procfile (defines the web, scheduler, and worker processes - also how heroku knows this is a python project)
      |-- wsgi.py (the python wsgi file that gunicorn actually uses)
      |-- uwsgi.ini (config for uwsgi)
      |-- djeroku.py (the script that helps set everything up on heroku)
      |-- urls.py (top level django url management)
      |-- tox.ini (tox config file)
      |-- manage.py (the django script that, well, manages everything)
      |-- project (the folder containing the code)
         |-- settings (all the settings for dev vs production)
            |-- common.py (settings used in both dev and production)
            |-- dev.py (settings for local development - generally easy setup)
            |-- prod.py (settings for production use - real settings and services)
         |-- celery.py (config for celery - mainly for auto-task discovery)
         |-- apps (the folder that will contain all the individual apps you write)
            |-- djeroku_app (finally, the app that actually drives the site -- will have all the models, tests, templates etc)
~~~
