import dagster as dg
from dagster_dbt import dbt_assets, DbtCliResource, DagsterDbtTranslator
from recommender_system.resources import dbt_project

class CustomDagsterDbtTranslator(DagsterDbtTranslator):
    """Custom dbt -> dasgter translator"""
    def get_group_name(self, dbt_resource_props) -> str:
        return 'dbt_group'
    def get_description(self, dbt_resource_props) -> str:
        return f"Dagster asset representing the dbt {dbt_resource_props['name']} model"

@dbt_assets(
        manifest=dbt_project.manifest_path,
        dagster_dbt_translator=CustomDagsterDbtTranslator(),
        )
def dbt_models(context: dg.AssetExecutionContext, dbt_resource: DbtCliResource):
    yield from dbt_resource.cli(["build"], context=context).stream()