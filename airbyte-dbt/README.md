# Parte I: Implementación de ELT en Airbyte-dbt

A continuacion se describen los pasos y comandos para ejecutar el flujo de obtención de la data (***Airbyte***) y transformación de la misma (***dbt***) utilizando un postgres server corriendo en Docker en el papel de warehouse.

## Ejecución

**Requisitos (entre paréntesis versiones utilizadas, no necesariamente requeridas)** 

- [Python](https://www.python.org) (**3.12.3**)
- [Docker Engine](https://docs.docker.com/engine/) (**27.5.1**)
- [Airbyte](https://airbyte.com) (**v0.24.0** - helm chart **v1.4.1**)

<br/>

**1. Clonar el repo**<br>
```bash
git clone https://github.com/tvillani22/MLOps.git && cd ITBA-MLOps/airbyte-dbt
```

<br/>

**2. Verificar requisitos y configurar el entorno**<br>
```bash
docker --version
abctl version
set -a; source .env; set +a
```

<br/>

**3. Configurar el entorno de python**<br>
```bash
python -m venv airbyte-dbt-env
source ./airbyte-dbt-env/bin/activate
pip install -r requirements.txt # (dbt dbt-postgres requests python-dotenv)
```

<br/>

**4. Levantar el container de postgres**<br>
```bash
docker pull postgres
docker run -d --rm \
    --name mlops-postgres \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    -v $POSTGRES_DATA_FOLDER:/var/lib/postgresql/data \
    -p $PGPORT:$PGPORT \
    --network $AIRBYTE_NETWORK_NAME \
    -h $PGHOST_KIND_NW \
    postgres
docker ps
```

<br/>

**5. Crear objetos necesarios en el postgres server**<br>

```bash
./scripts/setupwh.sh
```

<br/>

**6. Ejecutar el extract y load con *Airbyte***

En primer lugar, iniciar el contaner de ***kind*** que corre airbyte:
```bash
docker ps -a
docker container start airbyte-abctl-control-plane
docker ps
abctl local status
```

Con **Airbyte** ejecutándose se deben crear las fuentes para los tres archivos (especificando nombre, tipo, formato, url, etc), el postgres server como destino (especificando host, puerto, database, schema y credenciales) y finalmente las conexiones vinculando las mismas. Esto puede hacerse en la UI de forma interactiva o programáticamente via la API de Airbyte.

Con ello hecho, ya se pueden disparar los *sync* de cada una de las conexiones que traerán la data desde la fuente (en este caso un repo de GH) y la cargarán en el postgres server funcionando como warehouse. Análogamente, esto puede hacerse en la UI, o através de la API, como se implementa aquí con un pequeño script:

```bash
python scripts/trigger_airbyte_sync.py
```

<br/>

**7. Ejecutar transformación con *dbt***<br>

Como primer paso, se verifica que  **dbt-core** y el plugin para postgres están intalados y son compatibles:

```bash
dbt --version
```

Notar que no hace falta correr `dbt init` para crear todo la estructura (el *scaffold*) del proyecto porque eso ya está armado en el repo en el directorio `dbt_mlops_project`. Y de hecho se pueden inspeccionar los archivos de configuración dentro del mismo y verificar que todo esté en orden:

```bash
cd dbt_mlops_project
cat dbt_project.yml profiles.yml
dbt debug
```

Con todo validado, se ejecuta la transformación (y opcionalmente los tests):

```bash
dbt run
dbt test 
```

<br/>

**8. Finalización**<br>

Para finalizar, se deben detener ambos containers. Si no se quieren mantener los objetos creados en el postgres puede utilizarse un pequeño script que los eliminará y dejará solo lo que trae la imagen por default. 

```bash
./scripts/cleanupwh.sh
docker container stop mlops-postgres airbyte-abctl-control-plane
deactivate
```