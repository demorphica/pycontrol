#!/usr/bin/env python

import shlex, subprocess, sys, syslog
from time import time, sleep

user=sys.argv[1]
host=sys.argv[2]
duration=int(sys.argv[3])
runtime=int(sys.argv[4])
interval=int(sys.argv[5])

syslog.syslog(syslog.LOG_ALERT, "Checking host "+host+" for load status started")

def loadcheck(n):
        end_time = time() + n
        systemload = []
        while time() < end_time:
                try:
                        p_ssh = subprocess.Popen(shlex.split("/usr/bin/ssh "+user+"@"+host+" wmic cpu get LoadPercentage"), stdout=subprocess.PIPE)
                        p_awk = subprocess.Popen( shlex.split('awk "NR==2"'), stdin=p_ssh.stdout, stdout=subprocess.PIPE)
                        out, err = p_awk.communicate()
                except ValueError:
                        out = 0
                        syslog.syslog(syslog.LOG_ALERT, "loadAvg for host "+host+" could not be retreived, assuming 0%")
                try:
                        currentload=float(out)
                except ValueError:
                        currentload=0
                syslog.syslog(syslog.LOG_ALERT, "host "+host+" is "+str(currentload)+"% loaded")
                systemload.append(currentload)
                sleep(1)
        averageload = sum(systemload) / float(len(systemload))
        return averageload

def pingcheck(name):
        try:
                p_ping = subprocess.Popen(shlex.split("/bin/ping -q -c 1 -W 1 -w 2 "+name), stdout=subprocess.PIPE)
                p_lastrow = subprocess.Popen(shlex.split('/usr/bin/gawk "NR==4"'), stdin=p_ping.stdout, stdout=subprocess.PIPE)
                p_packetloss = subprocess.Popen(shlex.split("/usr/bin/gawk '{print $7}'"), stdin=p_lastrow.stdout, stdout=subprocess.PIPE)
                out, err = p_packetloss.communicate()
                packetloss=filter(type(out).isdigit, out)
        except ValueError:
                return 3
        if int(packetloss) == 100:
                return 0
        elif int(packetloss) == 0:
                return 1

def dohybridsleep(username, hostname):
        try:
                 p_sleep = subprocess.Popen(shlex.split("/usr/bin/ssh "+username+"@"+hostname+" psshutdown -d -t 01"), stdout=subprocess.PIPE)
                 out, err = p_sleep.communicate()
                 return(1)
        except ValueError:
                print("Could not determine success for sending sleep signal to host "+host)
                return(0)

def check(n):
        end_time = time() + n
        loadlastduration = []
        while time() < end_time:
                load=loadcheck(runtime)
                syslog.syslog(syslog.LOG_ALERT, "Average load for this test run is "+str(load)+"%")
                loadlastduration.append(load)
                sleep(interval)
        avgloadlastduration=sum(loadlastduration) / float(len(loadlastduration))
        if avgloadlastduration > 1.0:
                syslog.syslog(syslog.LOG_ALERT, "Host "+host+" is Working ...")
                sys.exit()
        elif avgloadlastduration <= 1.0:
                syslog.syslog(syslog.LOG_ALERT, "Host "+host+" is Idle")
                syslog.syslog(syslog.LOG_ALERT, "Sending sleep signal to host "+host)
                dohybridsleep(user, host)
                sys.exit()
        else:
                syslog.syslog(syslog.LOG_ALERT, "Could not reliably determine load for host "+host)
        sys.exit()

def main():
        ishostalive = pingcheck(host)
        if ishostalive == 3:
                syslog.syslog(syslog.LOG_ALERT, "ICMP echo request test check for "+host+"failed unexpectedly")
                sys.exit()
        elif ishostalive == 0:
                syslog.syslog(syslog.LOG_ALERT, "Host "+host+" is down")
                sys.exit()
        elif ishostalive == 1:
                check(duration)

if __name__ == '__main__':
        main()
