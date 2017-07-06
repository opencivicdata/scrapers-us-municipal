#!/bin/bash

# Make directory for project. This may already exist but it's a good practice
# to make sure this pipeline will work on a bare server.
mkdir -p /home/datamade/scrapers-us-municipal

# Decrypt files encrypted with blackbox
cd /opt/codedeploy-agent/deployment-root/$DEPLOYMENT_GROUP_ID/$DEPLOYMENT_ID/deployment-archive/ && chown -R datamade.datamade . && sudo -H -u datamade blackbox_postdeploy