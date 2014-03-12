Versa: Quick start on Postgres
==============================




createdb -U uche dendrite_sandox "DB for learning about and experimenting with Dendrite."


Debian, Ubuntu, etc.
--------------------

$ sudo apt-get install postgresql postgresql-contrib

Then create a user for versa

$ sudo -u postgres createuser -P -s versa

$ createdb -U uche versa_test "A temp DB for Versa test suite"

Useful links:

* http://www.itzgeek.com/featured/how-to-install-postgresql-9-1-3-with-pgadmin-3-on-ubuntu-11-10-linux-mint-12.html


Make sure you've changed the postgres user:

sudo -u postgres psql -d postgres -U postgres

postgres=# alter user postgres with password 'use_a_better_password';
postgres=# \q

