import warnings
import dagster as dg
from recommender_system.assets import airbyte, dbt, recommender_assets
from recommender_system.resources import airbyte_instance, dbt_resource, postgres_resource
from recommender_system.jobs import airbyte_job, dbt_job, training_job
from dagster_mlflow import mlflow_tracking

warnings.filterwarnings("ignore", category=dg.ExperimentalWarning)

defs = dg.Definitions(
    assets=[airbyte.airbyte_assets, dbt.dbt_models, *recommender_assets],
    jobs=[airbyte_job, dbt_job, training_job],
    resources={
          "airbyte_resource": airbyte_instance,
          "dbt_resource": dbt_resource,
          "postgres_resource": postgres_resource,
          'mlflow': mlflow_tracking,
          },
)