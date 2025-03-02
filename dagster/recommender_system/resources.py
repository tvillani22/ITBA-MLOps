import dagster as dg
from dagster_airbyte import AirbyteResource
from dagster_dbt import DbtCliResource, DbtProject
import pandas as pd
from sqlalchemy import create_engine


airbyte_instance = AirbyteResource(
        host=dg.EnvVar("AIRBYTE_HOST"),
        port=dg.EnvVar("AIRBYTE_PORT"),
        username=dg.EnvVar("AIRBYTE_WAREHOUSE_USER"),
        password=dg.EnvVar("AIRBYTE_INSTANCE_PASSWORD"),
        request_max_retries=5,
        request_timeout=60
    )

dbt_project_directory = dg.EnvVar("DBT_PROJECT_DIR").get_value()
dbt_project = DbtProject(project_dir=dbt_project_directory)
dbt_resource = DbtCliResource(project_dir=dbt_project)
dbt_project.prepare_if_dev()


class PostgresConnection(dg.ConfigurableResource):
    """Custom resource for connecting with Postgres Server currently playing warehosue role"""
    database: dg.String = dg.EnvVar("WAREHOUSE_DB")
    host: str = dg.EnvVar("PGHOST")
    port: dg.String = dg.EnvVar("PGPORT")
    user: dg.String = dg.EnvVar("AIRBYTE_WAREHOUSE_USER")
    password: dg.String = dg.EnvVar("AIRBYTE_WAREHOUSE_PASSWORD")

    def _get_engine(self):
        conn_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return create_engine(conn_string)

    def save_table(self, df: pd.DataFrame) -> None:
        pass

    def load_table(self, schema_:str, table_name: str) -> pd.DataFrame:
        logger = dg.get_dagster_logger()
        table_full_name = f"{self.database}.{schema_}.{table_name}"
        logger.info(f"Retrieving table {table_full_name} from PostgresCustomResource...")
        return pd.read_sql_table(table_name=table_name, con=self._get_engine(), schema=schema_)

postgres_resource = PostgresConnection()