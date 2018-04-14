#!/bin/bash  
if pgrep python; 
then 
	pkill -9 python;
else
	echo "No python processes to kill."
fi
