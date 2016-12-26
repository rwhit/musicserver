#!/bin/bash

# foreach process:
# - suspend
# - add children to list
# - kill
# - un-suspend

#set -e

# arg can be pid or exe name (per ps -C)
[[ $# -gt 0 ]] || { echo "Error: must supply at least one pid/process name"; exit 1; }

declare -a PIDS
declare LEN=0
declare POPPED

declare -a TO_KILL
declare KILL_LEN=0

function push {
  PIDS[$LEN]="$1"
  ((LEN++))
}

function pop {
  ((LEN--))
  POPPED=${PIDS[$LEN]}
  unset PIDS[$LEN]
}

function pushByName {
  local pid
  for pid in $(ps -o pid="" -C $1)
  do
    push $pid
  done
}

function pushChildren {
  local parent=$1
  local pid ppid
  while read pid ppid
  do
    [[ $ppid -eq $parent ]] && push $pid
  done < <(ps ax -opid="",ppid="" | grep $parent)
}

function pushToKill {
  echo "saving $1 to kill later"
  TO_KILL[$KILL_LEN]="$1"
  ((KILL_LEN++))
}

function popToKill {
  ((KILL_LEN--))
  POPPED=${TO_KILL[$KILL_LEN]}
  unset TO_KILL[$KILL_LEN]
}

while [[ $# -gt 0 ]]
do
  if [[ $1 =~ [0-9]+ ]]
  then
    push $1
  else
    pushByName $1
  fi
  shift
done

while [[ $LEN -gt 0 ]]
do
  pop
  pid=$POPPED
  echo "processing $pid, $(ps u -p $pid)"
  sudo kill -STOP $pid
  pushChildren $POPPED
  pushToKill $pid
done

while [[ $KILL_LEN -gt 0 ]]
do
  popToKill
  pid=$POPPED
  echo "killing $pid, $(ps u -p $pid)"
  sudo kill $pid
  sudo kill -CONT $pid
done
