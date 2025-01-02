import kopf
import logging
import time
import asyncio
import base64 
import os
import base64
import datetime
from uuid import uuid5, NAMESPACE_URL
from kubernetes import client, config, dynamic
from urllib import parse

status_provisioning : str = "PROVISIONING"
status_ready : str = "READY"
status_active : str = "ACTIVE"
media_types_merge_patch : str = "application/merge-patch+json"

group : str = "xlscsde.nhs.uk"
kind : str = "AnalyticsCrate"
plural : str = "analyticscrates"
version : str = "v1"
max_connections : int = 1000
max_connections_per_user : int = 1000
api_version : str = f"{group}/{version}"
kube_config = {}

kubernetes_service_host = os.environ.get("KUBERNETES_SERVICE_HOST")
if kubernetes_service_host:
    kube_config = config.load_incluster_config()
else:
    kube_config = config.load_kube_config()

api_client = client.ApiClient(kube_config)
core_api = client.CoreV1Api(api_client)
dynamic_client = dynamic.DynamicClient(api_client)
custom_api = dynamic_client.resources.get(api_version = api_version, kind = kind)
custom_objects_api = client.CustomObjectsApi()
apps_v1 = client.AppsV1Api(api_client)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.connect_timeout = 60
    settings.watching.server_timeout = 60

@kopf.on.create(group=group, kind=kind)
@kopf.on.update(group=group, kind=kind)
@kopf.on.resume(group=group, kind=kind)
async def crate_updated(body, **_):
    namespace = os.environ.get("NAMESPACE", "jupyterhub")
    print(f"Crate updated: {body}")

