import dagster as dg
from dagster_airbyte import load_assets_from_airbyte_instance

from recommender_system.resources import airbyte_instance

airbyte_assets = load_assets_from_airbyte_instance(
    airbyte=airbyte_instance,
    connection_to_asset_key_fn=lambda con, tbl: dg.AssetKey([f"{tbl}_raw"]),
    connection_meta_to_group_fn=lambda x: "airbyte_group",
    )