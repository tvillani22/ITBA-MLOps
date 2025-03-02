#!/bin/bash

PSQL_VARS=""
for varline in $(envsubst < ${DBT_AIRBYTE_PROJECT_ROOT_PATH}/.env); do  PSQL_VARS="$PSQL_VARS -v $varline"; done
psql -U postgres -h $PGHOST -p 5432  $PSQL_VARS -f ${DBT_AIRBYTE_PROJECT_ROOT_PATH}/scripts/cleanupwh.sql;