------Airbyte-dbt Objects
CREATE USER :"AIRBYTE_WAREHOUSE_USER" WITH ENCRYPTED PASSWORD :'AIRBYTE_WAREHOUSE_PASSWORD';
ALTER USER :"AIRBYTE_WAREHOUSE_USER" CREATEDB;
SET ROLE :"AIRBYTE_WAREHOUSE_USER";
CREATE DATABASE :WAREHOUSE_DB;