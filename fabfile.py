"""
Djeroku project fabfile.

Includes helpful commands for managing a project.

- heroku_setup
  One time setup for your project. Run this to create your heroku deployment
  targets. Creates both a staging and a production app on heroku, including
  all the necessary settings and free addons. Also creates a pipeline from
  staging to production and sets up the local git repository and heroku remotes.

- serve
  Syncs the db, runs any pending migrations, collects static assets, then runs
  the local development server by calling `python manage.py runserver`

- web
  Same as serve, but runs the web process using foreman instead of the django
  development server directly. Can sometimes simulate the production
  environment better than the debug server. You'll probably need to install
  some of the production requirements.

- worker
  Runs a celery worker to process background tasks your application creates.

- test
  Runs your tests using the django test runner.

- deploy_staging
  Deploys the current local master branch to staging by calling
  `git push staging master`, then syncs, migrates, and collects static.

- deploy_production
  Deploys the current local master branch to production by calling
  `git push production master`, then syncs, migrates, and collects static.

- promote_production
  Promotes the currently deployed staging environment to production by calling
  `heroku pipeline:promote`. This is a slightly better deployment process -
  first deploy to staging, then test that everything is working as expected,
  then promote it to move that exact slug to the production environment.


Deployment:
  You can deploy your app to staging by pushing master to the staging remote:
  `git push staging master`. This will build your project and make it accessible
  on staging-<your-app-name>.herokuapp.com. You almost certainly will want to
  then call `heroku run python manage.py syncdb`

  When the code on staging is ready for production, you can promote the staging
  slug to your production app by calling `heroku pipeline:promote` or `fab
  promote_production`.

"""

from fabric.contrib.console import confirm, prompt
from fabric.api import abort, env, local, settings, task
import string
import random
import platform
import subprocess
import re

HEROKU_ADDONS = (
    'heroku-postgresql:dev',
    'scheduler:standard',
    'redistogo:nano',
    'memcachier:dev',
    'newrelic:wayne',
    'mandrill:starter',
    'papertrail:choklad'
)

HEROKU_CONFIGS = (
    'DJANGO_SETTINGS_MODULE=project.settings.prod',
)

STAGING_REMOTE = 'staging'
PRODUCTION_REMOTE = 'production'


@task
def heroku_setup():
    """
    Set up everything you need on heroku. Creates a production app
    (remote: production) and a matching staging app (remote: staging) and
    does the following:

        - Create new Heroku applications.
        - Install all `HEROKU_ADDONS`.
        - Set all `HEROKU_CONFIGS`.
        - Initialize New Relic's monitoring add-on.

    https://devcenter.heroku.com/articles/multiple-environments

    NOTE: the production app will have ENVIRONMENT_TYPE=production while
    staging will have ENVIRONMENT_TYPE=staging if the code needs to know which
    environment it is running in (for example, so staging can use a
    non-production db follower)
    """
    app_name = prompt('What name should this heroku app use?', default='{{project_name}}')
    staging_name = '%s-staging' % app_name

    # create the apps on heroku
    cont('heroku apps:create %s --remote %s --addons %s' %
            (staging_name, STAGING_REMOTE, ','.join(HEROKU_ADDONS)),
            "Failed to create the staging app on heroku. Continue anyway?")
    cont('heroku apps:create %s --remote %s --addons %s' %
            (app_name, PRODUCTION_REMOTE, ','.join(HEROKU_ADDONS)),
            "Failed to create the production app on heroku. Continue anyway?")

    # set configs
    for config in HEROKU_CONFIGS:
        cont('heroku config:set %s --app=%s' % (config, staging_name),
            "Failed to set %s on Staging. Continue anyway?" % config)
        cont('heroku config:set %s --app=%s' % (config, app_name),
            "Failed to set %s on Production. Continue anyway?" % config)

    # set debug
    cont('heroku config:set DEBUG=True --app=%s' % staging_name,
        "Failed to set DEBUG on Staging. Continue anyway?")
    cont('heroku config:set DEBUG=False --app=%s' % app_name,
        "Failed to set DEBUG on Production. Continue anyway?")

    # set environment type
    cont('heroku config:set ENVIRONMENT_TYPE=staging --app=%s' % staging_name,
        "Failed to set ENVIRONMENT_TYPE on Staging. Continue anyway?")
    cont('heroku config:set ENVIRONMENT_TYPE=production --app=%s' % app_name,
        "Failed to set ENVIRONMENT_TYPE on Production. Continue anyway?")

    # set secret key on production
    cont('heroku config:set SECRET_KEY="%s" --app=%s' % (
            generate_secret_key(), app_name
        ),
        'Failed to set SECRET_KEY on Production. Continue anyway?'
    )

    # create a pipeline from staging to production
    pipelines_enabled = cont( 'heroku labs:enable pipelines',
            "Failed to enable Pipelines. Continue anyway?")
    if pipelines_enabled:
        pipeline_plugin = cont(
                'heroku plugins:install ' + \
                'git://github.com/heroku/heroku-pipeline.git',
            'Failed to install pipelines plugin. Continue anyway?')
        if pipeline_plugin:
            cont('heroku pipeline:add -a %s %s' % (staging_name, app_name),
                'Failed to create pipeline from Staging to Production. ' + \
                'Continue anyway?')

    # set git to default to staging
    local('git init')
    local('git config heroku.remote staging')

    # create git remotes
    local('heroku git:remote -r staging --app=%s' % staging_name)
    local('heroku git:remote -r production --app=%s' % app_name)

@task
def deploy_staging():
  """
  Deploys the current local master branch to staging by calling
  `git push staging master`, then syncs, migrates, and collects static.
  """
  local('git push staging master')
  after_deploy('staging')

@task
def deploy_production():
    """
    Deploys the current local master branch to production by calling
    `git push production master`, then syncs, migrates, and collects static.
    """
    local('git push production master')
    after_deploy('production')

@task
def promote_production():
    """Promotes the staging slug to production."""
    local('heroku pipeline:promote')

@task
def serve():
    """
    Sync db, migrate, collect static, and run the django
    development server.
    """
    venv('python manage.py syncdb')
    venv('python manage.py migrate')
    venv('python manage.py collectstatic --noinput')
    venv('python manage.py runserver')

@task
def web():
    """
    Sync db, migrate, collect static, and run the web
    process using foreman.
    """
    venv('python manage.py syncdb')
    venv('python manage.py migrate')
    venv('python manage.py collectstatic --noinput')
    venv('foreman start web')

@task
def worker():
    """Run a task queue worker."""
    venv('python manage.py celery worker')

@task
def test():
    """Run the django tests."""
    venv('python manage.py test')

########## HELPERS
def venv(cmd):
    if platform.system == 'Windows':
        # untested - good luck, windows people! (submit a working PR)
        return run('venv/bin/activate.bat && ' + cmd)
    return run('source venv/bin/activate && ' + cmd)

def after_deploy(remote):
    app_name = get_heroku_app_names()[remote]
    run('heroku run python manage.py syncdb --app=%s' % app_name)
    run('heroku run python manage.py migrate --app=%s' % app_name)
    run('heroku run python manage.py collectstatic --noinput --app=%s' % (
            app_name
        )
    )

def cont(cmd, message):
    with settings(warn_only=True):
        result = local(cmd, capture=True)

    if message and result.failed:
        print result.stderr
        if not confirm(message):
            abort('Stopped execution per user request.')
        return False
    return True

def run(cmd):
    return subprocess.call(cmd, shell=True)

def get_heroku_app_names():
    """Expects the default setup above."""
    p = subprocess.Popen(["git", "remote", "-v"], stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    lines = stdout.split("\n")

    pattern = r'(.*)\t.*heroku\.com/(.*)\.git (\(.*\))'
    remotes = {}
    for line in lines:
        match = re.match(pattern, line)
        if match:
            remotes[match.group(1)] = match.group(2)

    return remotes

def generate_secret_key(key_length=64):
    """Randomly generate a 64 character key you can stick in your
    settings/environment"""
    options = string.digits + string.letters + ".,!@#$%^&*()-_+={}"
    return ''.join([random.choice(options) for i in range(key_length)])
########## END HELPERS

