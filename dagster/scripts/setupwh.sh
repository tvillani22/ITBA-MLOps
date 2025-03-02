#!/bin/bash

PSQL_VARS=""
for varline in $(envsubst < ${DAGSTER_PROJECT_ROOT_PATH}/.env); do  PSQL_VARS="$PSQL_VARS -v $varline"; done
psql -U postgres -h $PGHOST -p 5432  $PSQL_VARS -f ${DAGSTER_PROJECT_ROOT_PATH}/scripts/setupwh.sql;