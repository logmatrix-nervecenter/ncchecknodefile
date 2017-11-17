#!/usr/bin/python3
# ----------------------------------------------------------------------------
# NerveCenter node list validator
#    LogMatrix, Inc (C) 2017
#
#  For help with this script contact Customer Support <support@logmatrix.com>
#
#  Does some simple integrity checks on a node file. 1> If the node file
#  contains nodes with ids, then it verifies the ids are unique. Node
#  files before NerveCenter v8 do not have ids. NerveCenter v8 will assign
#  a unique id to each node. 2> Verifies node names are unique. 3> Checks
#  whether any nodes are sharing the same IP Address. Note that this might
#  be what you want, so it is not necessarily an error.
#
#  You are welcome to copy and modify this script.
#
#  You can name a file to check or let it read the main node file.
#    $ ncchecknodefile
#  or
#    $ ncchecknodefile -f /opt/OSInc/db/nervecenter.node.backup
#
# History
#  2017-11-16 Created by Greg Moberg <gmoberg@logmatrix.com>
#
# ----------------------------------------------------------------------------

import sys, getopt

# the file to read
node_filename = '/opt/OSInc/db/nervecenter.node'

# boolean. whether to be talkative
verbose_mode=False

# name of this script
myname=sys.argv[0]

# ----------------------------------------------------------------------------
# myusage

def myusage():
     print('''
This command checks the integrity of a NerveCenter node file. It
reads but does not modify the indicated file.

Warnings and errors will be stated if enountered. When finished
it will state the file's node count and if any errors or warnings
were encountered.
''')
     print('usage:')
     print('    '+myname+' [-v] [-f <nodefile>]')
     print('  or')
     print('    '+myname+' [--verbose] [--file <nodefile>]')
     print('''
  -v | --verbose
        Talkative mode. Default is to be quiet and
        only speak up if something is wrong.

  -f | --filename
        Name a file to check. This defaults to
        file /opt/OSInc/db/nervecenter.node
''')

# ----------------------------------------------------------------------------
# main

try:
    user_options, user_values = getopt.getopt( sys.argv[1:], "f:hv",
                                               ["file=","help","verbose"])
    for opt, arg in user_options:
        if opt == '-h' or opt == '--help':
            myusage()
            sys.exit(0)
        elif opt == '-v' or opt == '--verbose':
            # let's be talkative
            verbose_mode=True
        elif opt == '-f' or opt == '--file':
            # arg has the filename. clean and remove any leading '='
            #   example: -f=/opt/OSInc/db/nervecenter.node
            arg=arg.strip()
            if arg[0] == '=':
                arg=arg[1:]
                arg=arg.strip()
            node_filename=arg
except getopt.GetoptError:
    myusage()
    sys.exit(2)

    
print('Checking node file '+node_filename)

# integer. the number of nodes found in the file
node_count=0

# integer. the number of warnings raised
warnings=0

# integer. the number of warnings raised
errors=0

# string. the ID of the node being looked at. this might not be used.
node_id=None

# string. the name of the node being looked at.
node_name=None

# string. the line number in the file where a node's definition begins
node_start_line=None

# a dictionary of where each node definition starts
#    example: node with name 'moose' begins on line 3
# this is used when we need to say where a node can be found in the file.
nodename_to_line = {}

# a dictionary of ipaddr-to-nodename(s)
#    example: ipaddress '192.168.1.1' is claimed by node with name 'moose'
# this is used to detect repetition of IP Addrs across nodes.
ipaddr_to_nodename = {}

# (If the node file does not have node ids then this is not in use)
# a dictionary of node-id-to-line assignments
#    example: node with id '339' begins on line 1904
# this is used to detect repetition of IDs across nodes.
nodeid_to_line = {}

# (If the node file does not have node ids then this is not in use)
# a dictionary of node-name-to-line assignments
#    example: node with name 'moose' has id '1'
# this is used to detect repetition of IDs across nodes.
nodename_to_id = {}

try:
  line_number = 0
  with open(node_filename, encoding='utf-8') as a_file:
    for line in a_file:
        line_number += 1
        line = line.strip()

        # parse the line into keyword and value
        elements = line.partition(" ")

        if 0 == len(elements[0]):
            # skip empty lines
            continue

        if 'begin' == elements[0] and 'node' == elements[2]:
            node_count += 1

            # remember where a node defn begins
            node_start_line = str(line_number)
            if verbose_mode:
                print('New node starting at line '+node_start_line)

        if 'end' == elements[0] and 'node' == elements[2]:
            # check whether this node has an id. this is of
            # interest only for node files that contain ids for nodes
            if 0 < len(nodeid_to_line) and node_id is None:
                warnings += 1
                print('WARNING: Node '+node_name+' at line '+node_start_line+
                      ' does not have an id')

            if verbose_mode:
                print('  ends at line '+str(line_number))

            # remember that a node defn has ended
            node_start_line = None
            node_id = None

        elif 'id' == elements[0]:
            # hold onto the current node id
            node_id = elements[2]

            if verbose_mode:
                print('  id '+node_id)

            # check whether any other node also has this id
            if node_id in nodeid_to_line:
                errors += 1
                print('ERROR: The nodes at line '+nodeid_to_line[node_id]+
                      ' and '+node_start_line+
                      ' both have the id '+node_id)
            else:
                nodeid_to_line[node_id] = node_start_line

        elif 'name' == elements[0]:
            # hold onto the current node name
            node_name = elements[2]

            if verbose_mode:
                print('  name '+node_name)

            # check whether any other node also has this name
            if node_name in nodename_to_line:
                errors += 1
                print('ERROR: The nodes at line '+nodename_to_line[node_name]+
                      ' and '+node_start_line+
                      ' both have the name '+node_name)
            else:
                nodename_to_line[node_name] = node_start_line
                
        elif 'address' == elements[0]:
            # hold onto the current node ip-address
            address = elements[2]

            if verbose_mode:
                print('  address '+address)

            # check whether any other node also has this ip-address
            if address in ipaddr_to_nodename:
                other_node_nodename = ipaddr_to_nodename[address]
                other_node_start_line = nodename_to_line[other_node_nodename]
                warnings += 1
                print('WARNING: Node '+node_name+' (line '+node_start_line+
                      ') and node '+other_node_nodename+' (line '+other_node_start_line+
                      ') both have ip address '+address)
            else:
                ipaddr_to_nodename[address] = node_name

  # end of file has been reached. this is the normal point of exit
  print('Finished. '+str(node_count)+' nodes, '+str(errors)+' errors'+str(warnings)+' warnings')

  result=0
  if 0 < errors:
    result=1
  sys.exit(result)

except FileNotFoundError:
    # we arrive here directly if the above 'with open' fails
    print('    Cannot access file '+node_filename)
    sys.exit(2)
# ----------------------------------------------------------------------------
# ###

