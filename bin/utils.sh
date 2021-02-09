##############################################################################
# Logs a message to a log file (or to console if argument is /dev/stdout)

logger () {
	MSG=$1
	
	# do nothing if logging is not enabled
	if [ "x1" != "x$LOGGING" ]; then
		return
	fi

	# if no logfile is specified, set a default
	if [ -z $LOGFILE ]; then
		$LOGFILE=stdout
	fi

	echo `date`: $MSG >> $LOGFILE
}


##############################################################################
# Retrieves the current time in seconds

currentTime () {
	date +%s
}


##############################################################################
# sets an RTC alarm
# arguments: $1 - time in seconds from now

wait_for () { 
	# calculate the time we should return
	ENDWAIT=$(( $(currentTime) + $1 ))

	# disable/reset current alarm
	echo 0 > /sys/class/rtc/rtc$RTC/wakealarm

	# set new alarm
	echo $ENDWAIT > /sys/class/rtc/rtc$RTC/wakealarm

	# check whether we could set the alarm successfully
	if [ $ENDWAIT -eq `cat /sys/class/rtc/rtc$RTC/wakealarm` ]; then
		logger "Start waiting for timeout ($1 seconds)"

		# wait for timeout to expire
		while [ $(currentTime) -lt $ENDWAIT ]; do
			REMAININGWAITTIME=$(( $ENDWAIT - $(currentTime) ))
			if [ 0 -lt $REMAININGWAITTIME ]; then
				# wait for device to suspend or to resume - this covers the sleep period during which the
				# time counting does not work reliably
				logger "Starting to wait for timeout to expire"
				lipc-wait-event -s $REMAININGWAITTIME com.lab126.powerd resuming || true
			fi
		done

		logger "Finished waiting"
	else
       		logger "Failure setting alarm on rtc$RTC, wanted $ENDWAIT, got `cat /sys/class/rtc/rtc$RTC/wakealarm`"
	fi

	# not sure whether this is required
	lipc-set-prop com.lab126.powerd -i deferSuspend 1
}
