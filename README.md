assh - select your servers from aws with ncurses and then ssh easily - or do something else with them.

How
==========================
assh brings a list of servers from your AWS account. Search, move, Hit enter to select one,
then ssh to them.

You can also add some other plugins - currently fabric and graphing cpu from cloudwatch is supported.

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

and then you can

    assh project ssh

select your fav. server and hit enter.

you can also extend and override commands in project.py file

    def cmd_SSH(self, line):
        return 'ssh -i ~/.ssh/project.pem ubuntu@%s' % line

Usage
===========================
