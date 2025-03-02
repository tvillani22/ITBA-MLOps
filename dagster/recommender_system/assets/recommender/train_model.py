import dagster as dg
from dagster import asset, AssetIn, Int, Float, multi_asset, AssetOut, Output, MetadataValue, List, String, AssetKey
import pandas as pd
from sklearn.model_selection import train_test_split

MLFLOW_REGISTERED_MODEL_NAME = "Movies_Recommender_Model"

@asset(
        deps=["scores_movies_users"],
        config_schema={
            'dbt_target_schema': dg.Field(dg.StringSource, is_required=True, description="Schema to locate the table")
            }
        )
def training_data(context: dg.AssetExecutionContext, postgres_resource: dg.ConfigurableResource) -> Output[pd.DataFrame]:
    """Training data casted and joined"""
    dbt_target_schema = context.op_config["dbt_target_schema"]
    training_data = postgres_resource.load_table(schema_=dbt_target_schema, table_name="scores_movies_users")
    return Output(
        training_data,
        metadata={
            "Total rows": len(training_data),
            "preview": MetadataValue.md(training_data.head().to_markdown()),
        },
    )


@multi_asset(
    ins={
        "training_data": AssetIn(
        )
    },
    outs={
        "preprocessed_training_data": AssetOut(description="Preprocessed ready to split"),
        "user2Idx": AssetOut(),
        "movie2Idx": AssetOut(),
    }
)
def preprocessed_data(training_data: pd.DataFrame):
    u_unique = training_data.user_id.unique()
    user2Idx = {o:i+1 for i,o in enumerate(u_unique)}
    m_unique = training_data.movie_id.unique()
    movie2Idx = {o:i+1 for i,o in enumerate(m_unique)}
    training_data['encoded_user_id'] = training_data.user_id.apply(lambda x: user2Idx[x])
    training_data['encoded_movie_id'] = training_data.movie_id.apply(lambda x: movie2Idx[x])
    preprocessed_training_data = training_data.copy()
    return (
        Output(
            preprocessed_training_data,
            metadata={
                "Total rows": len(preprocessed_training_data),
                "preview": MetadataValue.md(preprocessed_training_data.head().to_markdown()),
                }
        ),
        Output(
            user2Idx,
            metadata={
                "Total keys": len(user2Idx),
                "preview": str({k:v for k,v in list(user2Idx.items())[:3]}),
            },
        ),
        Output(
            movie2Idx,
            metadata={
                "Total keys": len(movie2Idx),
                "preview": str({k:v for k,v in list(movie2Idx.items())[:3]}),
            },
        ),
    )


@multi_asset(
    ins={
        "preprocessed_training_data": AssetIn(
    )
    },
    outs={
        "X_train": AssetOut(description="Features training set"),
        "X_test": AssetOut(description="Features evaluation set"),
        "y_train": AssetOut(description="Scores training set"),
        "y_test": AssetOut(description="Scores evaluation set"),
    },
    config_schema={
        'test_size': Float,
    }
)
def split_data(context, preprocessed_training_data):
    #test_size=0.10
    test_size = context.op_config["test_size"]
    random_state = 42
    X_train, X_test, y_train, y_test = train_test_split(
        preprocessed_training_data[['encoded_user_id', 'encoded_movie_id']],
        preprocessed_training_data[['rating']],
        test_size=test_size, random_state=random_state
    )
    msg = f"Using test split ratio {test_size*100}%"
    return (
        Output(
            X_train,
            metadata={
                "Total rows": len(X_train),
                "preview": MetadataValue.md(X_train.head().to_markdown()),
                }
        ),
        Output(
            X_test,
            metadata={
                "Total rows": len(X_test),
                "Note": msg,
                "preview": MetadataValue.md(X_test.head().to_markdown()),
            },
        ),
        Output(
            y_train,
            metadata={
                "Total rows": len(y_train),
                "preview": MetadataValue.md(y_train.head().to_markdown()),
            },
        ),
        Output(
            y_test,
            metadata={
                "Total rows": len(y_test),
                "Note": msg,
                "preview": MetadataValue.md(y_test.head().to_markdown()),
            },
        ),
    )


@asset(
    required_resource_keys = {'mlflow'},
    ins={
        "X_train": AssetIn(),
        "y_train": AssetIn(),
        "user2Idx": AssetIn(),
        "movie2Idx": AssetIn(),
    },
    config_schema={
        'batch_size': Int,
        'epochs': Int,
        'learning_rate': Float,
        'embeddings_dim': Int,
        'loss': String,
        "metrics": [String],
    }
)
def model_trained(context, X_train, y_train, user2Idx, movie2Idx):
    """Trained model"""
    from .model_helper import get_model
    from keras.src.optimizers.adam import Adam
    mlflow = context.resources.mlflow
    mlflow.log_params(context.op_config)
    registered_model_name = MLFLOW_REGISTERED_MODEL_NAME
    mlflow.tensorflow.autolog(
        registered_model_name=registered_model_name,
    )

    batch_size = context.op_config["batch_size"]
    epochs = context.op_config["epochs"]
    learning_rate = context.op_config["learning_rate"]
    embeddings_dim = context.op_config["embeddings_dim"]
    loss = context.op_config["loss"]
    metrics = context.op_config["metrics"]
    model = get_model(len(movie2Idx), len(user2Idx), embeddings_dim)
    model.compile(Adam(learning_rate=learning_rate), loss=loss, metrics=metrics)
    context.log.info(f'Training with batch_size: {batch_size} - epochs: {epochs}...')
    history = model.fit(
        [
            X_train.encoded_user_id,
            X_train.encoded_movie_id
        ], 
        y_train.rating, 
        batch_size=batch_size,
        epochs=epochs, 
        verbose=1
    )
    for i, l in enumerate(history.history['loss']):
        mlflow.log_metric('mse', l, i)
    from matplotlib import pyplot as plt
    fig, axs = plt.subplots(1)
    axs.plot(history.history['loss'], label='mse')
    plt.legend()
    mlflow.log_figure(fig, 'plots/loss.png')
    context.log.info(f'Registering the model as {MLFLOW_REGISTERED_MODEL_NAME}...')
    return Output(
            model,
            metadata={
                "Training details": f"Adam-trained using parameters {context.op_config}",
            },
        )


@asset(
    required_resource_keys = {'mlflow'},
    ins={
        "X_test": AssetIn(),
        "y_test": AssetIn(),
    },
    deps= ["model_trained"],
)
def model_metrics(context, X_test, y_test):
    """Evaluation metrics of the trained model"""
    mlflow = context.resources.mlflow
    run_id = mlflow.active_run().info.run_id
    logged_model_uri = f"runs:/{run_id}/model"
    loaded_model = mlflow.pyfunc.load_model(logged_model_uri)
    context.log.info(f'Evaluating model with URI {logged_model_uri}..')
    y_pred = loaded_model.predict([
            X_test.encoded_user_id,
            X_test.encoded_movie_id
    ])
    from sklearn.metrics import mean_squared_error

    mse = mean_squared_error(y_pred.reshape(-1), y_test.rating.values)
    metrics = {
        'test_mse': mse,
        'test_rmse': mse**(0.5)
    }
    mlflow.log_metrics(metrics)
    return metrics