---
title: AWMS Crate Operator
layout: page
parent:  Data Source Management
grand_parent: Architecture
---


The [AWMS](https://lsc-sde.github.io/lsc-sde/AWMS.html) Crate Operator is a component of the DataSource Management Capabilities of the solution.

# What does this component do?
The AWMS Crate Operator watches all resources of type [AnalyticsCrate](https://lsc-sde.github.io/lsc-sde/AMWS/Custom-Resources/AnalyticsCrates.html). Upon any create or update to these bindings, the operator create and maintain the [AnalyticsDataSource](https://lsc-sde.github.io/lsc-sde/AMWS/Custom-Resources/AnalyticsWorkspaceDataSources.html) objects based upon the information in the ro-crate definitions


# How does this component do it's task?
This component uses [KOPF](https://lsc-sde.github.io/lsc-sde/Developer-Guide/KOPF.html) to provide an operator model in kubernetes. 

When an create/update/resume action is received for an AnalyticsCrate object, it is created in kubernetes it:
* Checks the current commit id against the branch to see if it's already been processed, if so it will stop processing here
* Clone the repository using the details provided in the crate definition
* Read & validate the ro-crate metadata files and build an AnalyticsDataSource object based upon the information collected
* Create/update the AnalyticsDataSource object in kubernetes

# Component Details
## Permissions
The AWMS Crate Operator has the following permissions:

| Api Group | Resource | Permissions |
| --- | --- | --- |
| | namespaces | get, watch, list |
| | events | create |
| apiextensions.k8s.io | customresourcedefinitions | get, watch, list |
| admissionregistration.k8s.io | validatingwebhookconfigurations | create, patch |
| xlscsde.nhs.uk | analyticscrates | get, watch, list, patch |
| xlscsde.nhs.uk | analyticsworkspaces | get, watch, list, patch, create, delete |
| xlscsde.nhs.uk | analyticscrates/status | patch |
| xlscsde.nhs.uk | analyticscrates/scale | patch |
| kopf.dev | clusterkopfpeerings | list, watch, get, patch |