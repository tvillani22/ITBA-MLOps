# Parte II: Implementación en Dagster

A continuacion se describen los pasos y comandos para orquestar con **Dagster** el flujo de:
1. Extracción y carga de la data (**Airbyte**).
2. Transformación (**dbt**).
3. Preprocesamiento.
4. Entrenamiento, evaluación y registro de un modelo (trackeado con **MLflow**).

## Ejecución

**Requisitos (entre paréntesis versiones utilizadas, no necesariamente requeridas)** 
- [Airbyte](https://airbyte.com) (**v0.24.0** - helm chart **v1.4.1**)
- [Docker Engine](https://docs.docker.com/engine/) (**27.5.1**)
- [Docker Compose](https://docs.docker.com/compose/) (**v2.32.4**)
- [Poetry](https://python-poetry.org) (**v2.1.0**)
- [Python v3.12.*](https://www.python.org/downloads/release/python-3129/)

**1. Clonar el repo**<br>

```bash
git clone https://github.com/tvillani22/MLOps && cd ITBA-MLOps/dagster
```

<br/>

**2. Verificar requisitos y configurar el entorno**<br>

```bash
docker --version
abctl version
poetry --version
set -a; source .env; set +a
```

<br/>

**3. Configurar el entorno de python**<br>

```bash
poetry install 
poetry env info
poetry show | grep -E 'dbt|mlflow|postgres|airbyte|dagster|tensor'
```

Notar que aquí no hace falta correr los comandos `dbt init` y `dagster project scaffold` para crear toda la estructura (*scaffold*) del proyecto en esas herramientas, porque eso ya está armado en el repo en los directorios `dbt_mlops_project` y `dasgter`, respectivamente.

<br/>

**4. Levantar el container de kind corriendo *Airbyte***

```bash
docker ps -a
docker container start airbyte-abctl-control-plane
abctl local status
```

<br/>

**5. Levantar el servicio de postgres y crear objetos necesarios**<br>

```bash
docker compose up postgres
./scripts/setupwh.sh
```

<br/>

**6. Levantar el servicio de mlflow**<br>

Antes de levantar el servicio se debe, o bien proveer un archivo de credenciales de AWS en `./secrets/aws_credentials.txt` , o remover la opción `--default-artifact-root` del `docker-compose.yml` (L49) para que MLflow guarde los artefactos el path que por defecto utiliza como *artifact store* (`./mlruns/`).

La imagen a utilizar es la especificada en el [Dockerfile](docker/mlflow/dockerfile), basada en la [imagen oficial de mlflow](https://github.com/mlflow/mlflow/pkgs/container/mlflow).[^1] 

[^1]: Imagen disponible en el **GitHub Container Registry**.

```bash
docker pull ghcr.io/mlflow/mlflow
docker compose up mlflow
```

<br/>

**7. Ejecutar el flujo orquestando desde Dagster**<br>

>**NOTA**: *los siguientes comandos se preceden con `poetry run` para que se ejecuten dentro del environment creado por **Poetry***.

En primer lugar conviene validar todo el código a usar tanto en **dbt** como en **Dagster**:

```bash
poetry run dbt debug
poetry run dagster definitions validate
```

<br/>

Con ello validado, se debe levantar el webserver en local:

```bash
poetry run dagster dev
```

<br/>

Después de verificar el webserver corriendo, se pueden materializar los jobs:

```bash
poetry run dagster job list
```

<br/>

>**I. Extract y load con *Airbyte* (`airbyte_job`)**:
>```bash
>poetry run dagster job execute -m recommender_system.definitions -j airbyte_job 
>```

<br/>

>**II. Transformación con *dbt* (`dbt_job`)**:
>```bash
>poetry run dagster job execute -m recommender_system.definitions -j dbt_job
>```

<br/>

>**III. Preprocesamiento, entrenamiento, evaluación y registro trackeado con *MLflow* (`training_job`):**
>```bash
>poetry run dagster job execute -m recommender_system.definitions -j training_job
>```

<br/>

**8. Finalización:**<br>

Para finalizar, se deben detener los servicios corriendo en el compose y el webersver de dasgter.

```bash
./scripts/cleanupwh.sh
docker compose down 
SIGINT dasgter dev
```