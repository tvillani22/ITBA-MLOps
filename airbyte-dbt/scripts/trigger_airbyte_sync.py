import os
import logging
import requests
from dotenv import load_dotenv, dotenv_values

logging.getLogger().setLevel(logging.INFO)
load_dotenv(dotenv_path="../.env")

ROOT_PATH = os.getenv("DBT_AIRBYTE_PROJECT_ROOT_PATH")
AIRBYTE_HOST = os.getenv("AIRBYTE_HOST")
AIRBYTE_PORT = os.getenv("AIRBYTE_PORT")
AIRBYTE_WORKSPACE_NAME = os.getenv("AIRBYTE_WORKSPACE_NAME")
AIRBYTE_CREDENTIALS = dotenv_values(
    dotenv_path=f"{ROOT_PATH}/secrets/airbyte_credentials.txt"
    )
WEBAPP_URL = f"http://{AIRBYTE_HOST}:{AIRBYTE_PORT}"
TOKEN_URL = f"{WEBAPP_URL}/api/v1/applications/token"
TEMPLATE_URL =  f"{WEBAPP_URL}/api/public/v1/{{endpoint}}"

def get_auth_headers():
    logging.debug("Fetching token..")
    body = {**AIRBYTE_CREDENTIALS}
    response = requests.post(TOKEN_URL, json=body)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}

def get_workspace_id(workspace_name = AIRBYTE_WORKSPACE_NAME):
    url = TEMPLATE_URL.format(endpoint="workspaces")
    logging.info("Fetching default workspace id..")
    response = requests.get(url, headers=get_auth_headers())
    workspaces = [ws for ws in response.json()["data"] if ws["name"] == workspace_name]
    if not workspaces:
        raise ValueError(f"Workspace {workspace_name} does not exist in airbyte instance")
    return workspaces[0]["workspaceId"]

def get_connections(workspace_ids):
    url = TEMPLATE_URL.format(endpoint="connections" )
    params = {"workspaceIds": [workspace_ids]}
    logging.info("Fetching connections ids..")
    response = requests.get(url, params=params, headers=get_auth_headers())
    connections = [(conn["connectionId"], conn["name"]) for conn in response.json()["data"]]
    connections_list = [f"{conn[1]} (id {conn[0]})" for conn in connections]
    logging.info("Connections succesfully retrieved:\n\t" + "\n\t".join(connections_list))
    return connections

def trigger_sinc(connections):
    url = TEMPLATE_URL.format(endpoint="jobs")
    for connection_id, connection_name in connections:
        logging.info(f"Triggering sync for connection {connection_name} (id {connection_id})..")
        body = {
        "jobType": "sync",
        "connectionId": connection_id
        }
        requests.post(url, json=body, headers=get_auth_headers())

def main():
    workspace_id = get_workspace_id()
    connections = get_connections([workspace_id])
    trigger_sinc(connections)

if __name__ == "__main__":
    main()