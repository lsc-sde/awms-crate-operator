import os 
import logging
from lscsde_workspace_mgmt.models import (
    AnalyticsDataSource,
    AnalyticsCrate
)
from lscsde_workspace_mgmt.datasourceclient import AnalyticsDataSourceClient

from git import Repo
from pydantic import TypeAdapter
from uuid import uuid5, NAMESPACE_URL
from urllib.parse import urlparse
from kubernetes_asyncio.client import CoreV1Api, ApiException
from base64 import b64decode
import shutil
from rocrate.rocrate import (
    ROCrate
)

class GitProcessor:
    def __init__(self, core_api : CoreV1Api, ads_client : AnalyticsDataSourceClient):
        self.core_api = core_api 
        self.ads_client = ads_client
        self.namespace = os.getenv("NAMESPACE")
        self.log = logging.Logger("GitProcessor")

    async def process(self, body):
        adaptor = TypeAdapter(AnalyticsCrate)
        crate_resource : AnalyticsCrate = adaptor.validate_python(body)
        self.log.info(f"Crate {crate_resource.metadata.name} on {crate_resource.metadata.namespace} has been updated")
        
        id = uuid5(NAMESPACE_URL, crate_resource.spec.repo.url)
        path = f"/repos/{id}"

        if os.path.isdir(path):
            self.log.info(f"Removing {path} as already exists")
            shutil.rmtree(path)

        parsed_url = urlparse(crate_resource.spec.repo.url)
        if crate_resource.spec.repo.secret_name == None:
            crate_resource.spec.repo.secret_name = "pat-token"

        if crate_resource.spec.repo.secret_key == None:
            crate_resource.spec.repo.secret_key = "TOKEN"

        secret = await self.core_api.read_namespaced_secret(name = crate_resource.spec.repo.secret_name, namespace = self.namespace)
        secret_value = b64decode(secret.data[crate_resource.spec.repo.secret_key]).decode('utf-8')

        new_url = f"{parsed_url.scheme}://pat:{secret_value}@{parsed_url.hostname}{parsed_url.path}"
        
        self.log.info(f"Cloning URL {crate_resource.spec.repo.url} into {path}")
        repo = Repo.clone_from(new_url, path)

        commit_id = repo.head.commit.hexsha
        self.log.info(f"Latest Commit is {commit_id}")

        rocrate_path = f"{path}{crate_resource.spec.path}"
        self.log.info(f"Checking for file at {rocrate_path}")

        crate = ROCrate(path)

        replace_ds = True # Default behaviour is to replace the existing data source
        data_source = None
        try:
            data_source = await self.ads_client.get(crate_resource.metadata.namespace, crate_resource.metadata.name)
        except ApiException as e:
            if e.status == 404:
                self.log.info(f"DataSource '{crate_resource.metadata.name}' on '{crate_resource.metadata.namespace}' does not exist")       
                replace_ds = False # Data source doesn't exist so it will need to be created
                data_source = AnalyticsDataSource()    
                data_source.metadata.name = crate_resource.metadata.name
                data_source.metadata.namespace = crate_resource.metadata.namespace
            else:
                raise e    
                
        data_source.metadata.labels["xlscsde.nhs.uk/crate"] = crate_resource.metadata.name
        data_source.metadata.labels["xlscsde.nhs.uk/crateNamespace"] = crate_resource.metadata.namespace
        data_source.spec.display_name = crate.root_dataset.get("name")
        data_source.spec.description = crate.root_dataset.get("description")

        for e in crate.get_entities():
            self.log.info(f"Found {e.id} of type {e.type}")

            if e.type == "Project":
                data_source.spec.project.id = e.id
        
        self.log.info(f"Generated Data Source: {data_source}")
            
        self.log.info(f"Removing {path}")
        shutil.rmtree(path)

        if replace_ds == True:
            self.log.info(f"Updating Data Source {data_source.metadata.name} on {data_source.metadata.namespace}")
            await self.ads_client.replace(data_source)
        else:
            self.log.info(f"Data Source  {data_source.metadata.name} on {data_source.metadata.namespace} does not exist, creating")
            await self.ads_client.create(data_source)
        