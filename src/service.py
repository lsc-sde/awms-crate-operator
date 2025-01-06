import kopf
import logging
import time
import asyncio
import base64 
import os
import base64
import datetime
from uuid import uuid5, NAMESPACE_URL
from kubernetes_asyncio import client, config, dynamic
from lscsde_workspace_mgmt.eventclient import EventClient
from lscsde_workspace_mgmt.datasourceclient import AnalyticsDataSourceClient
from urllib import parse
from crate.processors import GitProcessor

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


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.watching.connect_timeout = 60
    settings.watching.server_timeout = 60

@kopf.on.create(group=group, kind=kind)
@kopf.on.update(group=group, kind=kind)
@kopf.on.resume(group=group, kind=kind)
async def crate_updated(body, **_):
    kube_config = {}

    kubernetes_service_host = os.environ.get("KUBERNETES_SERVICE_HOST")
    if kubernetes_service_host:
        kube_config = config.load_incluster_config()
    else:
        kube_config = await config.load_kube_config()

    api_client = client.ApiClient(kube_config)
    core_api = client.CoreV1Api(api_client)
    custom_objects_api = client.CustomObjectsApi()
    log = logging.Logger("EventClient")
    event_client = EventClient(api_client=api_client, log = log)
    ads_client = AnalyticsDataSourceClient(custom_objects_api, log, event_client)
    processor = GitProcessor(core_api, ads_client)
    await processor.process(body)    
