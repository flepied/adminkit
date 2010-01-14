#
# Regular cron jobs for the adminkit package
#
0 *	* * *	root	[ -x /usr/bin/adminkit ] && /usr/bin/adminkit
