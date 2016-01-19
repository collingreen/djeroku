"""
Djeroku setup file.

Creates a new djeroku project in the current directory. Includes
creating a virtualenvironment, installing dependencies, creating matching
staging and production projects on heroku, and provisioning the free heroku
addons djeroku expects.

Djeroku requires that you have pip, virtualenv, and git installed.

Usage:
    python create_djeroku_project.py project_name

    # for more info about what is going on
    python create_djeroku_project.py project_name --verbose
"""

import argparse
import sys
import logging
import os
import shutil
import platform
import re
import subprocess


CONFIG = {
    'virtualenv_folder': 'venv',
    'valid_project_name_regex': r'^[a-zA-Z]+[a-zA-Z0-9_-]*$',
    'temp_project_path_format': '_djeroku_temp_project_%d',
    'django_pip_version': '"django>=1.9,<1.10"',
    # point this to a local folder if you cloned djeroku locally
    'djeroku_template_path':
        'https://github.com/djeroku/djeroku/archive/master.zip',
    'dependencies': {
        'pip': 'pip -V',
        'virtualenv': 'virtualenv --version',
        'git': 'git --version'
        }
}


def run(cmd):
    return 0 == subprocess.call(cmd, shell=True)


def venv(project_name, cmd):
    return run('%s && %s' % (get_venv_command(project_name), cmd))


def get_venv_command(project_name=None):
    pattern = 'source %svenv/bin/activate'
    if platform.system == 'Windows':
        # untested - good luck, windows people! (submit a working PR)
        pattern = '%svenv/bin/activate.bat'

    project = project_name + os.path.sep if project_name else ''
    return pattern % project


def create_djeroku_project(project_name):
    """
    Create a new project folder in this directory. Will prompt you for a
    project name, then create a new django project using the latest djeroku
    project template, including creating a virtualenvironment and installing
    all the dependencies.
    """

    # create virtualenv folder if necessary
    venv_path = os.path.join(project_name, CONFIG['virtualenv_folder'])
    if not os.path.exists(venv_path):
        logging.info('creating virtual environment')
        run('virtualenv %s' % venv_path)
    else:
        logging.info('existing virtual environment found')

    # install django
    logging.info('installing django')
    venv(
        project_name,
        'pip install %s' % CONFIG['django_pip_version']
    )

    # create project in temp dir
    temp_count = 1
    while True:
        temp_project_path = CONFIG['temp_project_path_format'] % temp_count
        temp_count += 1
        if not os.path.exists(temp_project_path):
            break

    logging.info('creating temporary project filestructure')
    os.makedirs(temp_project_path)
    venv(
        project_name,
        'django-admin startproject --template=%s --extension=py,html %s %s' % (
            CONFIG['djeroku_template_path'], project_name, temp_project_path
        )
    )

    # move project contents to real dir
    for filename in os.listdir(temp_project_path):
        shutil.move(
            os.path.join(temp_project_path, filename),
            os.path.join(project_name, filename)
        )

    # remove temp dir
    os.rmdir(temp_project_path)

    # install the djeroku dependencies with pip
    logging.info('installing djeroku dependencies')
    venv(project_name, 'pip install -r %s/reqs/dev.txt' % project_name)

    # setup the project
    run_django_setup(project_name)

    print_welcome_message(project_name)

    return True


def check_dependencies(dependencies):
    logging.info('checking for dependencies')
    missing_dependencies = []
    for dependency_name, command in dependencies.items():
        logging.debug('- checking dependency: %s', dependency_name)
        found = _check_dependency(command)

        if not found:
            missing_dependencies.append(dependency_name)

    return dict(
        dependencies_met=len(missing_dependencies) == 0,
        missing=missing_dependencies
    )


def _check_dependency(command):
    devnull = open(os.devnull, 'wb')
    return 0 == subprocess.call(
        command,
        shell=True,
        stdout=devnull,
        stderr=subprocess.STDOUT,
        close_fds=True
    )


def run_django_setup(project_name):
    logging.info('running django setup commands')
    venv(project_name, 'python %s/manage.py makemigrations' % project_name)
    venv(project_name, 'python %s/manage.py migrate' % project_name)
    venv(
        project_name,
        'python %s/manage.py collectstatic --noinput' % project_name
    )


def print_welcome_message(project_name):
    print("""
%(project_name)s project created successfully!

Thanks for using djeroku! You now have an empty django project skeleton in
%(project_name)s/ ready for you to use. There is a new djeroku.py in your
project folder that contains helpful commands you will likely use while
developing.

Next Steps:
    # Change to your project directory and activate your virtual env:
    cd %(project_name)s
    %(venv_command)s

    # Run the one-time setup script to create your heroku projects:
    python djeroku.py heroku_setup

    # Create a new app inside the project/apps folder:
    mkdir project/apps/newappname
    django-admin.py startapp newappname project/apps/newappname

    # Run the dev server to view your project in your browser (localhost:8000)
    python djeroku.py serve

    # Check out the other djeroku.py helper commands
    python djeroku.py --help

Remember, while developing, make sure you activate your virtualenvironment
first or you will get errors about django or other libraries not being found
(djeroku.py does this for you automatically).

When you add new libraries to your project, be sure to add them to
reqs/common.txt so heroku correctly includes them in your builds.

Please file any issues at https://github.com/collingreen/djeroku.

Happy coding!""".format(
        project_name=project_name,
        venv_command=get_venv_command()
    ))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'project_name',
        help='name for new project'
    )
    parser.add_argument(
        '-v',
        '--verbose',
        help='increase output verbosity',
        action='store_true'
    )
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug('Log level set to debug')

    # check dependencies
    result = check_dependencies(CONFIG['dependencies'])
    if not result['dependencies_met']:
        for missing in result['missing']:
            logging.error('Missing required dependency `%s`', missing)
            logging.error('Dependencies not met - aborting project creation.')
            sys.exit(1)

    # abort if invalid project name
    if re.match(CONFIG['valid_project_name_regex'], args.project_name) is None:
        logging.error('invalid project name - aborting')
        sys.exit(1)

    # check for existing project folder
    if os.path.exists(args.project_name):
        logging.error('project folder %s already exists - aborting install')
        sys.exit(1)

    # create folder
    logging.info('creating project folder %s', args.project_name)
    os.makedirs(args.project_name)

    # create the project
    create_djeroku_project(args.project_name)

if __name__ == '__main__':
    main()
