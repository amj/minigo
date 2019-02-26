# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Overrideable configuration parameters
# To override, simple do
#   export PARAM=value

export PROJECT=${PROJECT:-"minigo-pub"}
export LOGGING_PROJECT=${PROJECT:-"$PROJECT"}
export BOARD_SIZE=${BOARD_SIZE:-"19"}

# Configuration for service accounts so that the cluster can do cloud-things.
export SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-"${PROJECT}-${CLUSTER_NAME}-services"}
export SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT}@${PROJECT}.iam.gserviceaccount.com"
export SERVICE_ACCOUNT_KEY_LOCATION=${SERVICE_ACCOUNT_KEY_LOCATION:-"/tmp/${SERVICE_ACCOUNT}-key.json"}

# Constants for docker container creation
export VERSION_TAG=${VERSION_TAG:-"v17"}
export EVAL_VERSION_TAG=${EVAL_VERSION_TAG:-"latest"}

# Bucket names live in a single global namespace
# So, we prefix the project name to avoid collisions
#
# For more details, see https://cloud.google.com/storage/docs/best-practices
export BUCKET_NAME=${BUCKET_NAME:-"${PROJECT}-minigo-${VERSION_TAG}-${BOARD_SIZE}"}

# By default, buckets are created in us-east1, but for more performance, it's
# useful to have a region located near the training cluster.
# For more about locations, see
# https://cloud.google.com/storage/docs/bucket-locations
export BUCKET_LOCATION=${BUCKET_LOCATION:-"us-central1"}

# Bigtable resources
export CBT_INSTANCE=${CBT_INSTANCE:-"minigo-instance"}
export CBT_ZONE=${CBT_ZONE:-"us-central1-b"}
export CBT_TABLE=${CBT_TABLE:-"games"}
export CBT_EVAL_TABLE=${CBT_EVAL_TABLE:-"eval_games"}

# Needed for Bigtable clients or any gRPC code running on a GCE VM
export GRPC_DEFAULT_SSL_ROOTS_FILE_PATH=/etc/ssl/certs/ca-certificates.crt
