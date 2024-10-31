#!/usr/bin/env bash
set -e

host="$1"
shift
cmd="$@"

until mariadb-admin ping -h "$host" -u root -pyourpassword --silent; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "MySQL is up - executing command"
exec $cmd


