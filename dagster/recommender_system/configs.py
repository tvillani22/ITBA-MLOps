mlflow_resources = {
    'mlflow': {
        'config': {
            'experiment_name': {'env': 'MLFLOW_EXPERIMENT_NAME'},
            'mlflow_tracking_uri': {'env': 'MLFLOW_TRACKING_URI'},
        }            
    },
}


training_config = {
    'model_trained': {
        'config': {
            'batch_size': 128,
            'epochs': 10,
            'learning_rate': 1e-3,
            'embeddings_dim': 5,
            'loss': 'mse',
            "metrics": ["mse"],
        }
    },
    'split_data': {
        'config': {
            'test_size': 0.2,
        }
    },
    'training_data': {
        'config': {
            'dbt_target_schema': {'env': 'WAREHOUSE_TARGET_SCHEMA'},
        }
    },
}


training_job_config = {
    'resources': {
        **mlflow_resources,
    },
    'ops': {
        **training_config
    }
}