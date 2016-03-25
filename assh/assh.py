#-*- coding: utf-8 -*-

import boto.ec2

import imp
import subprocess

def get_instances(region, aws_key, aws_secret, **tags):
    conn = boto.ec2.connect_to_region(region, # n virginia
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
from hst.hst import Picker, QuitException

import locale
locale.setlocale(locale.LC_ALL,"")

logger = logging.getLogger(__name__)


class SimpleLineLoader(object):
    def __init__(self, aws_region, aws_key, aws_secret):
        self.aws_key = aws_key
        self.aws_secret = aws_secret
        self.aws_region = aws_region

    def load(self):
        self.instances = get_instances(self.aws_region, self.aws_key, self.aws_secret)
        lines = []
        for i in self.instances:
            line = []
            line.append(i.public_dns_name.ljust(50))
            line.append(' | ')
            line.append(i.id.ljust(10))
            line.append(' | ')
            for k, v in i.tags.items():
                line.append('%s = %s' % (k, v))
            lines.append(' '.join(line))
        return lines


class AsshPicker(Picker):

    def get_hostname_from_line(self, line):
        return line.split('|')[0].strip()

    def get_instance_id_from_line(self, line):
        return line.split('|')[1].strip()

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

        if self.args.command:
            fn = getattr(self.settings, 'cmd_%s' % self.args.command.upper(), None)
            if fn:
                line = fn(self, line)
            else:
                fn = getattr(self, 'cmd_%s' % self.args.command.upper())
                line = fn(line)

        f = open(self.args.out, 'w')
        f.write(line.encode('utf8'))
        f.close()
        raise QuitException()

    def cmd_SSH(self, line):
        return 'ssh %s' % line

    def cmd_FAB(self, line):
        rest = subprocess.list2cmdline(self.args.rest)
        return 'fab -H %s %s' % (line, rest)

    def get_instance_by_public_ip(self, public_ip):
        for i in self.loader.instances:
            if i.public_dns_name == public_ip:
                return i

    def cmd_GRAPH_CPU(self, line):
        instance = self.get_instance_by_public_ip(line)
        import boto.ec2.cloudwatch
        import datetime
        cw = boto.ec2.cloudwatch.connect_to_region(self.loader.aws_region,
                                                   aws_access_key_id=self.loader.aws_key,
                                                   aws_secret_access_key=self.loader.aws_secret)
        stats = cw.get_metric_statistics(
            300,
            datetime.datetime.utcnow() - datetime.timedelta(seconds=3200),
            datetime.datetime.utcnow(),
            'CPUUtilization',
            'AWS/EC2',
            'Average',
            dimensions={'InstanceId':[instance.id]}
        )

        stats = sorted(stats, key=lambda x: x['Timestamp'])

        import plotly
        from plotly.graph_objs import Scatter, Layout
        plotly.offline.plot({
        "data": [
            Scatter(x=[i['Timestamp'] for k, i in enumerate(stats)], y=[i['Average'] for i in stats])
        ],
        "layout": Layout(
                title="CPU - %s" % instance.id,
                yaxis=dict(range=[0, 100])
            )
        })

        return "see the browser\n"

    def cmd_INFO(self, line):
        instance_info = """
id
groups - A list of Group objects representing the security groups associated with the instance.
public_dns_name - The public dns name of the instance.
private_dns_name - The private dns name of the instance.
state - The string representation of the instance’s current state.
state_code - An integer representation of the instance’s current state.
previous_state - The string representation of the instance’s previous state.
previous_state_code - An integer representation of the instance’s current state.
key_name - The name of the SSH key associated with the instance.
instance_type - The type of instance (e.g. m1.small).
launch_time - The time the instance was launched.
image_id - The ID of the AMI used to launch this instance.
placement - The availability zone in which the instance is running.
placement_group - The name of the placement group the instance is in (for cluster compute instances).
placement_tenancy - The tenancy of the instance, if the instance is running within a VPC. An instance with a tenancy of dedicated runs on a single-tenant hardware.
kernel - The kernel associated with the instance.
ramdisk - The ramdisk associated with the instance.
architecture - The architecture of the image (i386|x86_64).
hypervisor - The hypervisor used.
virtualization_type - The type of virtualization used.
product_codes - A list of product codes associated with this instance.
ami_launch_index - This instances position within it’s launch group.
monitored - A boolean indicating whether monitoring is enabled or not.
monitoring_state - A string value that contains the actual value of the monitoring element returned by EC2.
spot_instance_request_id - The ID of the spot instance request if this is a spot instance.
subnet_id - The VPC Subnet ID, if running in VPC.
vpc_id - The VPC ID, if running in VPC.
private_ip_address - The private IP address of the instance.
ip_address - The public IP address of the instance.
platform - Platform of the instance (e.g. Windows)
root_device_name - The name of the root device.
root_device_type - The root device type (ebs|instance-store).
block_device_mapping - The Block Device Mapping for the instance.
state_reason - The reason for the most recent state transition.
interfaces - List of Elastic Network Interfaces associated with this instance.
ebs_optimized - Whether instance is using optimized EBS volumes or not.
instance_profile - A Python dict containing the instance profile id and arn associated with this instance.
        """

        ret = []
        our_instance = self.get_instance_by_public_ip(line)
        for ln in instance_info.split("\n"):
            if ln:
                kv = ln.split('-')
                k = kv[0].strip()
                if k:
                    ret.append(u"%s: %s" % (k.decode('utf8'), getattr(our_instance, k, '')))
        return "%s\n" % '\n'.join(ret)

def assh():
    parser = argparse.ArgumentParser()

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
                        default=',',
                        help="seperator in for multiple selection - ie. to join selected lines with ; etc.")

    parser.add_argument("-r", "--replace",
                        default=' ',
                        help="replace with this in eval string. ie. hst -r '__' --eval='cd __ && ls'")

    parser.add_argument("-l", "--logfile",
                        default='assh.log',
                        help="where to put log file in debug mode")

    parser.add_argument("account", type=str,
                    help="aws account")

    parser.add_argument("command", type=str, nargs='?',
                    help="command - eg. ssh, fab")


    parser.add_argument('rest', nargs=argparse.REMAINDER)


    args = parser.parse_args()


    if args.debug:
        logger.setLevel(logging.DEBUG)
        hdlr = logging.FileHandler(args.logfile)
        logger.addHandler(hdlr)
    else:
        logger.setLevel(logging.CRITICAL)

    settings = imp.load_source('settings', '%s/.assh/%s.py' % (os.path.expanduser('~'), args.account))

    AsshPicker.settings = settings

    main(args,
         picker_cls=AsshPicker,
         loader=SimpleLineLoader(
             settings.AWS_REGION,
             settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY))

if __name__ == '__main__':
    assh()