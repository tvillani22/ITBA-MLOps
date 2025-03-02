import dagster as dg
from . import recommender

recommender_assets = dg.load_assets_from_package_module(
    package_module=recommender, group_name='recommender_group'
)