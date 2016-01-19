#! env/python

"""Usage:
  djeroku.py <command> [<args>...]
  djeroku.py help <command>
  djeroku.py -h | --help
{command_list}

Options:
  -h --help            show this help message and exit

See 'djeroku help <command>' for more information on a specific command.
"""
import sys
import logging
import string
import random
import platform
import subprocess
import re

logging.basicConfig(format='')


HEROKU_ADDONS = (
    'heroku-postgresql:hobby-dev',
    'scheduler:standard',
    'redistogo:nano',
    'memcachier:dev',
    'mailgun:starter',
    'papertrail:choklad'
)

HEROKU_CONFIGS = (
    'DJANGO_SETTINGS_MODULE=project.settings.prod',
)

STAGING_REMOTE = 'staging'
PRODUCTION_REMOTE = 'production'


# Tools for generating help content and managing commands

def abort(message, code=1):
    logging.error(message)
    sys.exit(code)


def command(func):
    """
    Command decorator. Wrap functions that should become commands. Docstrings
    are automatically used to create help text.

    @command
    def command_name(x, y, z):
        pass
    """
    func._is_command = True
    return func


@command
def help(command_name=None, *args):
    if command_name is None or command_name == 'help':
        abort("Help Error - Specify a command name for more information")

    try:
        command = find_command(command_name)
    except AttributeError:
        abort("Could not find command {command_name}".format(
            command_name=command_name
        ))

    doc = command.__doc__
    if doc is None:
        print(
            "No help information found for command {command_name}".format(
                command_name=command_name
            )
        )
    else:
        print(doc)


def get_all_commands():
    this_script = sys.modules[__name__]

    return {
        func_name: getattr(this_script, func_name)
        for func_name in dir(this_script)
        if hasattr(getattr(this_script, func_name), '_is_command')
    }


def find_command(command_name):
    commands = get_all_commands()
    if command_name in commands.keys():
        return commands[command_name]
    raise AttributeError('No command found for %s' % command_name)

# End Tools


@command
def heroku_setup():
    """
    heroku_setup

    One-time setup with everything you need on heroku. Creates a production app
    (remote: production) and a matching staging app (remote: staging) and
    does the following:

        - Initialize a local git repository.
        - Create new Heroku applications and set them up as git remotes.
        - Install all `HEROKU_ADDONS`.
        - Set all `HEROKU_CONFIGS`.

    https://devcenter.heroku.com/articles/multiple-environments

    NOTE: the production app will have ENVIRONMENT_TYPE=production while
    staging will have ENVIRONMENT_TYPE=staging if the code needs to know which
    environment it is running in (for example, so staging can use a
    non-production db follower)

    """
    app_name = prompt(
        'What name should this heroku app use?',
        default='{{project}}'
    )
    staging_name = '%s-staging' % app_name

    # create git repository
    run('git init')

    # create the apps on heroku
    cont(
        'heroku apps:create %s --remote %s --addons %s' %
        (staging_name, STAGING_REMOTE, ','.join(HEROKU_ADDONS)),
        'Failed to create the staging app on heroku. Continue anyway?'
    )

    cont(
        'heroku apps:create %s --remote %s --addons %s' %
        (app_name, PRODUCTION_REMOTE, ','.join(HEROKU_ADDONS)),
        'Failed to create the production app on heroku. Continue anyway?'
    )

    # set configs
    for config in HEROKU_CONFIGS:
        cont(
            'heroku config:set %s --app=%s' % (config, staging_name),
            'Failed to set %s on Staging. Continue anyway?' % config
        )
        cont(
            'heroku config:set %s --app=%s' % (config, app_name),
            'Failed to set %s on Production. Continue anyway?' % config
        )

    # set debug
    cont(
        'heroku config:set DEBUG=True --app=%s' % staging_name,
        'Failed to set DEBUG on Staging. Continue anyway?'
    )
    cont(
        'heroku config:set DEBUG=False --app=%s' % app_name,
        'Failed to set DEBUG on Production. Continue anyway?'
    )

    # set environment type
    cont(
        'heroku config:set ENVIRONMENT_TYPE=staging --app=%s' % staging_name,
        'Failed to set ENVIRONMENT_TYPE on Staging. Continue anyway?'
    )
    cont(
        'heroku config:set ENVIRONMENT_TYPE=production --app=%s' % app_name,
        'Failed to set ENVIRONMENT_TYPE on Production. Continue anyway?'
    )

    # set secret key on production
    cont(
        'heroku config:set SECRET_KEY="%s" --app=%s' % (
            generate_secret_key(),
            app_name
        ),
        'Failed to set SECRET_KEY on Production. Continue anyway?'
    )

    # set git to default to staging
    run('git config heroku.remote staging')

    # create git remotes
    run('heroku git:remote -r staging --app=%s' % staging_name)
    run('heroku git:remote -r production --app=%s' % app_name)


@command
def migrate():
    """
    migrate

    Runs any pending migrations by calling `python manage.py migrate`
    """
    venv('python manage.py migrate')


@command
def collect_static():
    """
    collect_static

    Collects all the static assets for your apps by calling
    `python manage.py collectstatic --noinput`
    """
    venv('python manage.py collectstatic --noinput')


@command
def serve():
    """
    serve

    Runs any pending migrations, collects static assets, then
    runs the local development server by calling `python manage.py runserver`
    """
    migrate()
    collect_static()
    venv('python manage.py runserver 0.0.0.0:8000')


@command
def web():
    """
    web

    Same as serve, but runs the web process using foreman instead of the django
    development server directly. Can sometimes simulate the production
    environment better than the debug server. You'll probably need to install
    some of the production requirements.
    """
    migrate()
    collect_static()
    venv('foreman start web')


@command
def worker():
    """
    worker

    Runs a celery worker to process background tasks your application creates.
    """
    venv('python manage.py celery worker')


@command
def test():
    """
    test

    Runs your tests using the django test runner.
    """
    venv('python manage.py test')


@command
def lint():
    """
    lint

    Runs flake8 on everything inside the project folder.
    """
    venv('flake8 project')


@command
def deploy(remote_name='staging'):
    """
    deploy <staging|production>

    Deploys the current local master branch to the target remote (default:
    staging) by calling `git push REMOTE master`, then migrates and
    collects static.
    """
    run('git push {remote} master'.format(remote=remote_name))
    after_deploy(remote_name)


# Helper functions

def venv(cmd):
    if platform.system == 'Windows':
        # untested - good luck, windows people! (submit a working PR)
        return run('venv/bin/activate.bat && ' + cmd)
    return run('. venv/bin/activate && ' + cmd)


def after_deploy(remote):
    app_name = get_heroku_app_names()[remote]
    heroku_run('python manage.py migrate', app_name)
    heroku_run('python manage.py collectstatic --noinput', app_name)


def cont(cmd, message):
    result = run(cmd, capture=True)
    print(result['stdout'].decode())
    if message and result['failure']:
        logging.error(result['stderr'].decode())
        if not confirm(message):
            abort('Stopped execution per user request.')
        return False
    return True


def confirm(message):
    print(message)
    print("Y/N")
    choice = input()
    return choice.lower() in ['y', 'yes']


def prompt(message, default=None):
    if default is not None:
        print("{message} (default: {default}):".format(
            message=message,
            default=default
        ))
    else:
        print(message)
    return input()


def heroku_run(command, app_name):
    run('heroku run {command} --app={app_name}'.format(
        command=command,
        app_name=app_name
    ))


def run(cmd, capture=False):
    if capture:
        proc = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        failure = proc.returncode > 0

        return dict(
            stdout=stdout,
            stderr=stderr,
            returncode=proc.returncode,
            failure=failure,
            success=not failure
        )

    else:
        return subprocess.call(cmd, shell=True)


def get_heroku_app_names():
    """Expects the default setup above."""
    proc = subprocess.Popen(["git", "remote", "-v"], stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    lines = stdout.split("\n")

    pattern = r'(.*)\t.*heroku\.com/(.*)\.git (\(.*\))'
    pattern2 = r'(.*)\s+.*heroku.*:(.*)\.git \(.*\)'
    remotes = {}
    for line in lines:
        match = re.match(pattern, line)
        if match:
            remotes[match.group(1)] = match.group(2)
        else:
            match2 = re.match(pattern2, line)
            if match2:
                remotes[match2.group(1)] = match2.group(2)

    return remotes


def generate_secret_key(key_length=64):
    """
    Randomly generate a 64 character key you can stick in your
    settings/environment
    """
    options = string.digits + string.ascii_letters + ".,!@#$%^&*()-_+={}"
    return ''.join([random.choice(options) for i in range(key_length)])


def print_usage():
    usage = __doc__

    commands = get_all_commands()
    commands_list = """
Commands:"""

    for command_name in commands.keys():
        commands_list += """
  {command_name}""".format(command_name=command_name)

    print(usage.format(
        command_list=commands_list
    ))


# End Helpers


if __name__ == '__main__':
    command_name, arguments = 'usage', []
    invocation = sys.argv[0]
    if len(sys.argv) > 1:
        command_name = sys.argv[1]
        arguments = sys.argv[2:]

    if command_name in ['-h', '--help', 'usage']:
        print_usage()
        sys.exit(0)

    command_function = find_command(command_name)
    command_function(*arguments)
