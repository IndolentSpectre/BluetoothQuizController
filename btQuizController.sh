#!/bin/bash
#
# Shell for btQuizController.py

python3 ./btQuizController.py &
export QPID=$!
echo "QPID = $QPID"

while [ A$ANS != "AQ" ]
do
	echo -n "Command (R=reset game, U=unlock all but current answerer, Q=quit): "
	read ANS CRAP
	case $ANS in
		R|r) kill -SIGHUP $QPID && echo "Game reset" || echo "Error in command"
		;;
		U|u) kill -SIGUSR2 $QPID && echo "Players unlocked" || echo "Error in command"
		;;
		Q|q) kill -SIGINT $QPID && echo "Game over" || echo "Error in command"
			break
			;;
	esac
done

