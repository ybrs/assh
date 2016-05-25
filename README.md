assh - select your servers from aws with ncurses and then ssh easily - or do something else with them.

[![asciicast](https://asciinema.org/a/2ga28o9gnondowm60ol7iad69.png)](https://asciinema.org/a/2ga28o9gnondowm60ol7iad69)

How
==========================
assh brings a list of servers from your AWS account. Search, move, Hit enter to select one,
then ssh (or whatever you want) to them.

Its extendible, so you can add some other commands - use it with fabric, ansible, ssh etc.


Why
==========================
Because servers come and go, and i started hating the questions "Do we have 2 appservers in X project or 3 ? ", "was it app4.x.project.com or app5.x.project.com".

Installation
=========================
use pip to install

    pip install assh

then create a python file in your ~/.assh directory with somename

    mkdir ~/.assh
    vim ~/.assh/project.py

add your AWS account info

    AWS_ACCESS_KEY_ID = 'XXXXX'
    AWS_SECRET_ACCESS_KEY = 'YYYY'
    AWS_REGION = 'us-east-1'

a region also can be a list eg
    AWS_REGION = ['us-east-1', 'us-east-2']

and then you can

    assh project ssh

select your fav. server and hit enter.

you can also extend and override commands in project.py file

    def cmd_SSH(self, line):
        return 'ssh -i ~/.ssh/project.pem ubuntu@%s' % line


Usage
===========================

using fabric

    assh project fab -P -- 'uptime && df -h'

    assh project fab -P uptime

    assh project ssh

    assh project graph_cpu

you can also filter by tags

    # show only worker instances - ones tagged with Role as worker
    assh --filter-tag=Role:worker project ssh

    # if we can only show one instance we don't show curses ui and jump directly to command
    assh --filter-tag=Name:app1 project ssh

    # because filtering with name is so common there is a shortcut
    assh -N app1 project ssh

    # we can pipe the servers name to another application with noop command
    assh -N app1 project noop | xargs ssh -i ~/.ssh/foo.pem

