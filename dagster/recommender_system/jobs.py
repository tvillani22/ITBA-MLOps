import dagster as dg
from recommender_system.configs import training_job_config
from recommender_system.assets.dbt import dbt_models

airbyte_job = dg.define_asset_job(
    name='airbyte_job',
    selection=dg.AssetSelection.groups("airbyte_group"),
    config={}
)

dbt_job = dg.define_asset_job(
    name='dbt_job',
    selection=[dbt_models],
    config={}
)

training_job = dg.define_asset_job(
            name="training_job",
            selection=dg.AssetSelection.groups('recommender_group'),
            config=training_job_config
        )