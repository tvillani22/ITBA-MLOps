from dagster import asset, define_asset_job, Output, String, AssetIn, FreshnessPolicy, MetadataValue
import pandas as pd

MAX_FRESHNESS_LAG_MIN=5


#------------------------------------ASSETS------------------------------------#

@asset(
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=MAX_FRESHNESS_LAG_MIN),
    code_version="2",
    config_schema={
        'uri': String
    },
)
def movies(context) -> Output[pd.DataFrame]:
    uri = context.op_config["uri"]
    result = pd.read_csv(uri)
    return Output(
        result,
        metadata={
            "Total rows": len(result),
            "preview": MetadataValue.md(result.head().to_markdown()),
        },
    )

@asset(
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=MAX_FRESHNESS_LAG_MIN),
    config_schema={
        'uri': String
    }
)
def users(context) -> Output[pd.DataFrame]:
    uri = context.op_config["uri"]
    result = pd.read_csv(uri)
    return Output(
        result,
        metadata={
            "Total rows": len(result),
            "preview": MetadataValue.md(result.head().to_markdown()),
        },
    )

@asset(
    freshness_policy=FreshnessPolicy(maximum_lag_minutes=MAX_FRESHNESS_LAG_MIN),
    required_resource_keys = {'mlflow'},
    config_schema={
        'uri': String
    }
)
def scores(context) -> Output[pd.DataFrame]:
    mlflow = context.resources.mlflow
    uri = context.op_config["uri"]
    result = pd.read_csv(uri)
    metrics = {
        "Total rows": len(result),
        "scores_mean": float(result['rating'].mean()),
        "scores_std": float(result['rating'].std()),
        "unique_movies": len(result['movie_id'].unique()),
        "unique_users": len(result['user_id'].unique())
    }
    mlflow.log_metrics(metrics)
    return Output(
        result,
        metadata={
            **metrics,
            "preview": MetadataValue.md(result.head().to_markdown())
        }
    )

@asset(ins={
    "scores": AssetIn(),
    "movies": AssetIn(),
    "users": AssetIn(),
})
def training_data(users: pd.DataFrame, movies: pd.DataFrame, scores: pd.DataFrame) -> Output[pd.DataFrame]:
    scores_users = pd.merge(scores, users, left_on='user_id', right_on='id')
    all_joined = pd.merge(scores_users, movies, left_on='movie_id', right_on='id')

    return Output(
        all_joined,
        metadata={
            "Total rows": len(all_joined),
            "preview": MetadataValue.md(all_joined.head().to_markdown()),
        },
    )


#------------------------------------CONFIGS------------------------------------#
mlflow_resources = {
    'mlflow': {
        'config': {
            'experiment_name': {'env': 'MLFLOW_EXPERIMENT_NAME'},
            'mlflow_tracking_uri': {'env': 'MLFLOW_TRACKING_URI'},
        }            
    },
}

data_ops_config = {
    'movies': {
        'config': {
            'uri': 'https://raw.githubusercontent.com/mlops-itba/Datos-RS/main/data/peliculas_0.csv'
            }
    },
    'users': {
        'config': {
            'uri': 'https://raw.githubusercontent.com/mlops-itba/Datos-RS/main/data/usuarios_0.csv'
            }
    },
    'scores': {
        'config': {
            'uri': 'https://raw.githubusercontent.com/mlops-itba/Datos-RS/main/data/scores_0.csv'
            }
    }
}

job_data_config = {
    'resources': {
        **mlflow_resources
    },
    'ops': {
        **data_ops_config,
    }
}


#------------------------------------JOB------------------------------------#

data_job = define_asset_job(
    name='get_data',
    selection=['movies', 'users', 'scores', 'training_data'],
    config=job_data_config
)

