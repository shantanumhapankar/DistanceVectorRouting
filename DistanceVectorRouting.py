#!/usr/bin/python

import sys
import os
from socket import *
import pprint
import time
from threading import Event, Thread
import ast

dv = {}
linkcontents = {}
seqnum = 1
class RepeatedTimer:

    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = Thread(target=self._target)
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        return self.interval - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()

def UDPsend(ip, port):
    broadcast = socket(AF_INET, SOCK_DGRAM)
    broadcast.sendto(str(dv),(ip, port))
    broadcast.close()


def BroadcastThread():
    global dv, seqnum
    for items in dv:
        if items != 'host':
            UDPsend(dv[items]['ip'], dv[items]['port'])
    print "output number " + str(seqnum)
    seqnum += 1
    PrintLink(dv)

def CheckCostChange(filepath):
    global dv, linkcontents
    while(True):
        test = InitDv(filepath)
        pp = pprint.PrettyPrinter()
        if test != linkcontents:
            # pp.pprint(test)
            # pp.pprint(linkcontents)
            # linkcontents = test
            for (k1,v1), (k2,v2) in zip(test.items(), linkcontents.items()):
                if k1 != 'host' and  k2 != 'host':
                    if k1 == k2:
                        if v1['cost'] != v2['cost']:
                            dv[k1]['cost'] = v1['cost']
                            linkcontents = test
                            pp.pprint(dv)

def GetNumOfNeighbours(filepath):
    numofneighbours = 0
    with open(filepath, 'r') as f:
        numofneighbours = f.readline()
    return numofneighbours

def PrintLink(distancevector):
    for key, value in distancevector.iteritems():
        if key != 'host':
            print 'shortest path '+ dv['host'] + '-' + key +': the next hop is ' + value['nexthop']+' and the cost is '+str(value['cost'])

def InitDv(filepath):
    routingtable = {}
    file = os.path.basename(filepath)
    host = file.split('.')[0]
    routingtable['host'] = host
    with open(filepath, 'r') as f:
        lines = f.readlines()[1:]
        # data.update(dict(line.split() for line in lines))
        for line in lines:
            split = line.split()
            routingtable[split[0]] = {'nexthop': split[0], 'cost': float(split[1]), 'port':  int(split[2]), 'ip': split[3]}
    return routingtable

def UpdateDv(receivedpacket):
    global dv
    host = receivedpacket['host']
    if host in dv:
        for key, value in receivedpacket.iteritems():
            if key != 'host' and key != dv['host']:
                if key in dv:
                    currcost = dv[key]['cost']
                    newcost = dv[host]['cost'] + value['cost']
                    if (newcost < currcost):
                        dv[key]['nexthop'] = host
                        dv[key]['cost'] = newcost
                else:
                    newcost = dv[host]['cost'] + value['cost']
                    dv[key] = {'nexthop': host, 'cost': newcost, 'port':  value['port'], 'ip': value['ip']}

def main():
    global dv, linkcontents
    try:
        if len(sys.argv) != 3:
            print "Please check the arguments passed."
            sys.exit("Usage: ./DistanceVectorRouting.py <port> </Data/file>")

        port = int(sys.argv[1]) 
        file = sys.argv[2]

        filepath = os.getcwd() + "/" + file

        if not os.path.isfile(filepath):
            sys.exit("This directory does not exist")

        print "------------------Starting Distance Vector Algorithm------------------"
        # pp = pprint.PrettyPrinter()
        dv = InitDv(filepath)
        linkcontents = dv
        print "Printing Initial Routing costs..."
        PrintLink(dv)

        numofneighbours = GetNumOfNeighbours(filepath)

        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('', port))

        broadcast = RepeatedTimer(15, BroadcastThread)
        checkfile = Thread(target=CheckCostChange, args = (filepath,))
        checkfile.start()

        while True:
            packet, addr = s.recvfrom(1024)
            packet = ast.literal_eval(packet)
            UpdateDv(packet)

    except KeyboardInterrupt:
        print " "
        print "Shutting down Server...."
        broadcast.stop()
        checkfile.stop()
        s.close()
        sys.exit(0)

if __name__ == "__main__":
    main()