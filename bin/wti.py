#!/usr/bin/env python
####################################################################
# $Id$
# by Andrew C. Uselton <uselton2@llnl.gov> 
# Copyright (C) 2000 Regents of the University of California
# See ./DISCLAIMER
####################################################################

import sys
import commands
import string
import getopt
import os
import fcntl, FCNTL

def usage(msg):
    print "usage:", sys.argv[0], "[-a] [-c conf] [-f fan] [-l ldir] [-q] [-w node,...] [on | off | reset]"
    print "-a       = on/off/reset all nodes"
    print "-c conf  = configuration file (default: <ldir>/etc/bogus.conf)"
    print "-f fan   = fanout for parallelism (default: 256 where implemented)"
    print "-l ldir  = powerman lirary directory (default: /usr/lib/powerman)"
    print "-q       = be quiet about any errors that may have occurred"
    print "-w nodes = comma separated list of nodes"
    print "-w -     = read nodes from stdin, one per line"
    print "on       = turn on nodes (the default)"
    print "off      = turn off nodes"
    print "reset    = reset nodes"
    print msg
    sys.exit(0)

def init(f):
    "Read in the node name port address for each node from the configuration file"
    ports = {}
    line = f.readline()
    while (line):
        tokens = string.split(line)
        line = f.readline()
	if(len(tokens) < 2):
            continue
        if (tokens[0][0] == '#'): continue
        ports[tokens[0]] = tokens[1]
    return ports

# initialize globals
powermandir  = '/usr/lib/powerman/'
config_file = 'etc/wti.conf'
verbose     = 1
names       = []
com         = '1'
all         = 0
fanout      = 256
tty         = '/dev/ttyD23'
password    = ''

# Look for environment variables and set globals

try:
    test = os.environ['POWERMANDIR']
    if (os.path.isdir(test)):
        powermandir = test
except KeyError:
    pass

# Parse the command line, check for sanity, and set globals

try:
    opts, args = getopt.getopt(sys.argv[1:], 'ac:f:l:qw:')
except getopt.error:
    usage("Error processing options\n")

if(not opts):
    usage("provide a list of nodes")

for opt in opts:
    op, val = opt
    if (op == '-a'):
        all = 1
    elif (op == '-c'):
        config_file = val
    elif (op == '-f'):
        fanout = val
    elif (op == '-l'):
        powermandir  = val
    elif (op == '-q'):
        verbose = 0
    elif (op == '-w'):
        if (val == '-'):
            name = sys.stdin.readline()
            while (name):
                if (name[-1:] == '\n'):
                    name = name[:-1]
                names.append(name)
                name = sys.stdin.readline()
        else:
            names = string.split(val, ',')
    else:
        usage("Unrecognized option " + op + "\n")

# Check for level of permision and restrict activities for non-root users

stat, uid = commands.getstatusoutput('/usr/bin/id -u')
if (stat == 0):
    if (uid != '0'):
        if(verbose):
            sys.stderr.write("wti: You must be root to run this\n")
        sys.exit(1)
else:
    if(verbose):
        sys.stderr.write("wti: Error attempting to id -u\n")
    sys.exit(1)

try:
    if (args and args[0]):
        if (args[0] == 'off'):
            com = '0'
        elif (args[0] == 'on'):
            com = '1'
        elif (args[0] == 'reset'):
            com = 'T'
        else:
            if(verbose):
                sys.stderr.write("wti: Unrecognized command " + args[0] + "\n")
            sys.exit(1)
except TypeError:
        if(verbose):
            sys.stderr.write("wti: Internal Error: " + args + " should be a list with one element\n")
        sys.exit(1)

if (powermandir):
    if (powermandir[-1] != '/'):
        powermandir = powermandir + '/'
    if(os.path.isdir(powermandir)):
        sys.path.append(powermandir)
        config_file = powermandir + config_file
    else:
        if(verbose):
            sys.stderr.write("wti: Couldn\'t find library directory: " + powermandir + "\n")
        sys.exit(1)
else:
    if(verbose):
        sys.stderr.write("wti: Couldn\'t find library directory: " + powermandir + "\n")
    sys.exit(1)
    
try:
    f = open(config_file, 'r')
    ports = init(f)
    f.close()
except IOError :
    if(verbose):
        sys.stderr.write("wti: Couldn\'t find configuration file: " + config_file + "\n")
    sys.exit(1)
    
# Carry out the action.  This will
# attempt to send to every valid node, even if some of those named
# are not legitimate targets, but it will only send to known
# legitimate targets
if(all):
    names = ports.keys()

try:
    f = open(tty, 'r+')
except IOError:
    if(verbose):
        sys.stderr.write ("wti: Unable to access wti control device on port " + tty + "\n")
    sys.exit()
try:
    fcntl.lockf(f.fileno(), FCNTL.LOCK_EX | FCNTL.LOCK_NB)
except IOError:
    if(verbose):
        sys.stderr.write ("wti: Unable to gain exclusive lock on icebox control device on port " + tty + "\n")
    sys.exit(1)

for name in names:
    try:
        port = ports[name]
        f.write(password+port+com+'\r\n')
    except KeyError:
        pass
fcntl.lockf(f.fileno(), FCNTL.LOCK_UN)
f.close()

sys.exit(0)

