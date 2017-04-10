#!/bin/sh

echo "Preparing BigSense Init >>"
envsubst  < /opt/bigsense/mssql-db-init.sql > /tmp/init.sql
cat /tmp/init.sql
while ! /opt/mssql-tools/bin/sqlcmd -S bigsense-db-mssql -U SA -P $SA_PASSWORD -i /tmp/init.sql
do
  echo "SQL Error Retrying in 5 sec"
  sleep 5
done
echo "SQL Completed Successfully"
