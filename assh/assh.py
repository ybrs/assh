import boto.ec2

import imp


def get_instances(aws_key, aws_secret,**tags):
    conn = boto.ec2.connect_to_region('us-east-1', # n virginia
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret)

    filters = {}
    if tags:
        filter_tags = {}
        for tn, tv in tags.iteritems():
            filter_tags[tn] = tv
        filters.update(tags)
    filters.update({'instance-state-name':'running'})

    reservations = conn.get_all_instances(filters=filters)
    instances = []
    for r in reservations:
        for i in r.instances:
            instances.append(i)
    return instances

# print get_hosts()
from hst.hst import main
import argparse
import logging
import os
import sys
if os.name != 'posix':
    sys.exit('platform not supported')
import curses
from operator import itemgetter
import logging
import os
import sys
import argparse
import thread
import time

import locale
locale.setlocale(locale.LC_ALL,"")

logger = logging.getLogger(__name__)


class SimpleLineLoader(object):
    def __init__(self, aws_key, aws_secret):
        self.aws_key = aws_key
        self.aws_secret = aws_secret

    def load(self):
        self.instances = get_instances(self.aws_key, self.aws_secret)
        lines = []
        for i in self.instances:
            line = []
            line.append(i.public_dns_name.ljust(50))
            line.append(' | ')
            for k, v in i.tags.items():
                line.append('%s = %s' % (k, v))
            lines.append(' '.join(line))
        return lines


from hst.hst import Picker, QuitException



class AsshPicker(Picker):

    def get_hostname_from_line(self, line):
        return line.split('|')[0].strip()

    def key_ENTER(self):
        line = self.pick_line()
        self.no_enter_yet = False
        logger.debug("selected_lineno: %s", line)

        if len(self.multiple_selected) == 0:
            self.multiple_selected = [line]

        line = self.args.separator.join([self.get_hostname_from_line(l) for l in self.multiple_selected])

        logger.debug("selected line: %s", line)

        if self.args.eval:
            if self.args.replace:
                line = self.args.eval.replace(self.args.replace, line)
            else:
                line = "%s %s" % (self.args.eval, line)

        f = open(self.args.out, 'w')
        f.write(line.encode('utf8'))
        f.close()
        raise QuitException()


def assh():
    parser = argparse.ArgumentParser()
    parser.add_argument("account", type=str,
                    help="aws account")

    parser.add_argument("-o", "--out", type=str,
                    help="output to file")
    parser.add_argument("-d", "--debug",
                    help="debug mode - shows scores etc.")
    parser.add_argument("-i", "--input",
                    help="input file")

    parser.add_argument("-e", "--eval",
                    help="evaluate command output")

    parser.add_argument("-p", "--pipe-out", action='store_true',
                    help="just echo the selected command, useful for pipe out")

    parser.add_argument("-I", "--separator",
                        default=' ',
                        help="seperator in for multiple selection - ie. to join selected lines with ; etc.")

    parser.add_argument("-r", "--replace",
                        default=' ',
                        help="replace with this in eval string. ie. hst -r '__' --eval='cd __ && ls'")

    parser.add_argument("-l", "--logfile",
                        default='hst.log',
                        help="where to put log file in debug mode")
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        hdlr = logging.FileHandler(args.logfile)
        logger.addHandler(hdlr)
    else:
        logger.setLevel(logging.CRITICAL)

    settings = imp.load_source('settings', '%s/.assh/%s.py' % (os.path.expanduser('~'), args.account))
    main(args,
         picker_cls=AsshPicker,
         loader=SimpleLineLoader(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY))

if __name__ == '__main__':
    assh()