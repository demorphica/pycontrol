#!/usr/bin/env python

import shlex, subprocess, sys, syslog
from time import time, sleep

username=sys.argv[1]
hostname=sys.argv[2]
duration=int(sys.argv[3])
runtime=int(sys.argv[4])
interval=int(sys.argv[5])

#ipaddr, hwaddr, duration, runtime, interval

class Host:

    def __init__(self, user, host, duration, runtime, interval):

        self.username=user
        self.hostname=host
        self.duration=duration
        self.runtime=runtime
        self.interval=interval

    def pingcheck(self):

        try:
                p_ping = subprocess.Popen(shlex.split("/bin/ping -q -c 1 -W 1 -w 2 "+self.hostname), stdout=subprocess.PIPE)
                p_lastrow = subprocess.Popen(shlex.split('/usr/bin/gawk "NR==4"'), stdin=p_ping.stdout, stdout=subprocess.PIPE)
                p_packetloss = subprocess.Popen(shlex.split("/usr/bin/gawk '{print $7}'"), stdin=p_lastrow.stdout, stdout=subprocess.PIPE)
                out, err = p_packetloss.communicate()
                packetloss=filter(type(out).isdigit, out)
        except ValueError:
                syslog.syslog(syslog.LOG_ALERT, "ICMP echo request test check for "+self.hostname+"failed unexpectedly")
                return 3
        if int(packetloss) == 100:
                syslog.syslog(syslog.LOG_ALERT, "ICMP echo request test resulted in 100% packets lost. Host "+self.hostname+" is down")
                return 0
        elif int(packetloss) == 0:
                syslog.syslog(syslog.LOG_ALERT, "ICMP echo request test succeded Host "+self.hostname+" is up")
                return 1

    def sleep(self):
        try:
                p_sleep = subprocess.Popen(shlex.split("/usr/bin/ssh "+self.username+"@"+self.hostname+" psshutdown -d -t 01"), stdout=subprocess.PIPE)
                out, err = p_sleep.communicate()
                return(1)
        except ValueError:
                print("Could not determine success for sending sleep signal to host "+self.hostname)
                return(0)

    def wake(self):
        try:
            p_gethwaddr1=subprocess.Popen(shlex.split("/bin/grep -A 1 -e "+self.hostname+" /etc/config/dhcp"), stdout=subprocess.PIPE)
            p_gethwaddr2=subprocess.Popen(shlex.split("/bin/grep -e mac"), stdin=p_gethwaddr1.stdout, stdout=subprocess.PIPE)
            p_gethwaddr3=subprocess.Popen(shlex.split("/usr/bin/gawk '{print$3}'"), stdin=p_gethwaddr2.stdout, stdout=subprocess.PIPE)
            out, err = p_gethwaddr3.communicate()
            out.replace("'", "")
            p_wake = subprocess.Popen(shlex.split("/usr/bin/etherwake -D -i eth0 "+out), stdout=subprocess.PIPE)
            out, err = p_wake.communicate()
            syslog.syslog(syslog.LOG_ALERT, "Sent WoL packet to host"+self.hostname)
            return(1)
        except ValueError:
            syslog.syslog(syslog.LOG_ALERT, "Error sending  WoL packet to host"+self.hostname)
            return(0)

    def check(self):
        end_time = time() + self.duration
        loadlastduration = []
        while time() < end_time:
                load=self.loadcheck()
                syslog.syslog(syslog.LOG_ALERT, "Average load for this test run is "+str(load)+"%")
                loadlastduration.append(load)
                syslog.syslog(syslog.LOG_ALERT, "Will resume test run after "+str(self.interval)+" seconds ...")
                sleep(self.interval)
        avgloadlastduration=sum(loadlastduration) / float(len(loadlastduration))
        syslog.syslog(syslog.LOG_ALERT, "Average load for all test runs is "+str(avgloadlastduration)+"%")
        return avgloadlastduration

    def loadcheck(self):
        end_time = time() + self.runtime
        systemload = []
        while time() < end_time:
                try:
                        p_ssh = subprocess.Popen(shlex.split("/usr/bin/ssh "+self.username+"@"+self.hostname+" wmic cpu get LoadPercentage"), stdout=subprocess.PIPE)
                        p_awk = subprocess.Popen( shlex.split('awk "NR==2"'), stdin=p_ssh.stdout, stdout=subprocess.PIPE)
                        out, err = p_awk.communicate()
                except ValueError:
                        out = 0
                        syslog.syslog(syslog.LOG_ALERT, "loadAvg for host "+self.hostname+" could not be retreived, assuming 0%")
                try:
                        currentload=float(out)
                except ValueError:
                        currentload=0

                syslog.syslog(syslog.LOG_ALERT, "host "+self.hostname+" is "+str(currentload)+"% loaded")
                systemload.append(currentload)
                sleep(1)
        averageload = sum(systemload) / float(len(systemload))
        return averageload

def main():

    host=Host(username, hostname, duration, runtime, interval)
    syslog.syslog(syslog.LOG_ALERT, "Checking host "+host.username+" for load status started")
    ishostalive =host.pingcheck()
    if ishostalive == 3:
        sys.exit()
    elif ishostalive == 0:
        host.wake()
        sys.exit()
    elif ishostalive == 1:
        status=host.check()
        if status > 1.0:
            sys.exit()
        elif status <= 1.0:
            syslog.syslog(syslog.LOG_ALERT, "Host "+host.username+" has been Idle for "+str(host.duration)+" seconds now")
            syslog.syslog(syslog.LOG_ALERT, "There is no demand for host "+host.username+". Sending sleep signal to host "+host.username)
            host.sleep()
            sys.exit()
        else:
            syslog.syslog(syslog.LOG_ALERT, "Could not reliably determine load for host "+host.username)
            sys.exit()

if __name__ == '__main__':
    main()
