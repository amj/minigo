#!/bin/bash

set -e

#TODO pull in ringmaster & networks here.
#gsutil cp $RINGMASTER_CONTROL docker_ring.ctl

echo "Running Ringmaster:"
cat docker_ring.ctl

/mg_venv/bin/ringmaster docker_ring.ctl run

echo "Ringmaster all done"
POD_NAME=`hostname | rev | cut -d'-' -f 1 | rev`

gsutil -m cp -r docker_ring.* gs://$OUTPUT_NAME/$POD_NAME/

