pycontrol
=========

pycontrol is a set of python scripts that can be used to control a remote Windows pc or HTPC. Power management for idle systems is included. This is meant to be used to remotely turn on (based on demand) turn off (based on load and other reasons, and control (run, kill, manage) other applications and Windows tools from a remote Linux system such as OpenWRT or Raspbian. This purpose of these scripts is to facilitate a smart HTPC and on demand PC system environment

Fpllow activity at http://demorphica.com/content/pycontrol-htpc-controller-your-home

Releaselog
==========

+++GNTP Notifications are now available, use growl++++
+++
+++Code cleanup, added syslog logging+++
+++First commit, procedural code+++

Usage
=========

user=sys.argv[1]
host=sys.argv[2]
duration=int(sys.argv[3])
runtime=int(sys.argv[4])
interval=int(sys.argv[5])


eg. /root/hostcheck.py windowsusername hostname 60 10 5

You can setup cron to run like this for eg.:

*/5 * * * * /root/hostcheck.py windowsusername hostname 60 10 5

The above command will start the script every 5 minutes, after starting, the script first checks if the host is alive by sending 2 ICMP packets (ping), if the host is alive, then a 60 second load investigation is done. The load checker will then do a test run by sending 1 wmic requests over ssh each second to the windows PC and then calculates the mean to find the loadavg for 10 seconds. The load checker will sleep for 5 seconds. The load check and sleep cycle will repeat till 60 seconds have passed. Then the aggregate load average is calculated by finding the average of all load check runs. 

If the load average is 1.0% over the entire duration, i.e sys.argv[3], a sleep signal is sent to the remote pc. It is assumed that psshutdown (search for it on a search engine) is available on the path of the remote pc. If the system load average is more than 1.0% then the scripts exits normally


The sleep interval (i.e sys.argv[5]) can be tuned to spread the system load check across the duration, (i.e sys.argv[3]) to achieve a better picture of the overall system load across a time without sending too many requests.

Activity logs are available on syslog, so you can run:

tailf /var/log/message
or tailf -f /var/log messages
or logread -f 

depending on which linux distro you are on, to see the logs.

needs passwordless ssh to work. Use an SSH server on windows and use openssh (if in Openwrt see: http://wiki.openwrt.org/inbox/replacingdropbearbyopensshserver) because there are passwordless ssh issues with the ssh client and i've tested it only to work with the openssh ssh client. For a windows SSH sever you may try Bitvise SSH server or do an internet search.



License
=========

Use GPLv3

TODOs
=========

Use config file
Add REST API over, control with cron and curl<br>
Daemonize<br>
Add host.startapplication(name) functionality to start application "name" on the remote host. (eg. start XBMC after waking, stop Virtualbox VMs before sleeping)<br>
Virtualbox management - looking at Oracle supported ways to hook in
Add demand enumeration (eg. wake sleeping host if network sees a UPNP request, or sleeping host is pinged by someone)<br>
Add power usage widgets via Flex
Add process controller UI via Flex+FDT - FDT license requested - ++FDT developers, if you see, this, please grant me a license!++
