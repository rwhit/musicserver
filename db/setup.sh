sudo -u postgres psql -c "create role pi with login createdb;"
createdb pi
psql -f ./init.sql
