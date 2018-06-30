// Copyright 2018 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "cc/dual_net/inference_server.h"

#include <atomic>
#include <functional>
#include <map>
#include <string>
#include <utility>
#include <vector>

#include "absl/memory/memory.h"
#include "absl/strings/str_cat.h"
#include "absl/time/time.h"
#include "cc/check.h"
#include "grpc++/grpc++.h"
#include "proto/inference_service.grpc.pb.h"

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;
using grpc::StatusCode;

namespace minigo {

namespace internal {

// Implementation of the InferenceService.
// The client InferenceServer pushes inference requests onto
// InferenceServiceImpl's request queue.
class InferenceServiceImpl final : public InferenceService::Service {
 public:
  // TODO(tommadams): try having the InferenceServer keep track of how many
  // InferenceClients are actively wanting to make inference requests (and their
  // desired batch size). That way it should be possible to know exactly how
  // many inference requests to wait for when batching.
  InferenceServiceImpl(int max_game_batch_size, int inference_batch_size)
      : max_game_batch_size_(max_game_batch_size),
        inference_batch_size_(inference_batch_size),
        batch_id_(1) {}

  Status GetConfig(ServerContext* context, const GetConfigRequest* request,
                   GetConfigResponse* response) override {
    response->set_board_size(kN);
    response->set_batch_size(inference_batch_size_);
    return Status::OK;
  }

  Status GetFeatures(ServerContext* context, const GetFeaturesRequest* request,
                     GetFeaturesResponse* response) override {
    std::vector<RemoteInference> game_batches;

    {
      // std::cerr << absl::Now() << " START GetFeatures\n";

      // Lock get_features_mutex_ while popping inference requests off the
      // request_queue_: we want make sure that each request fills up as much
      // of a batch as possible. If multiple threads all popped inference
      // requests off the queue in parallel, we'd likely end up with multiple
      // partially empty batches.
      absl::MutexLock lock(&get_features_mutex_);
      // std::cerr << "### GetFeatures" << std::endl;

      // Each client is guaranteed to never request more than
      // max_game_batch_size_ inferences in each RemoteInference. Additionally,
      // each client is only able to have one pending RemoteInference at a
      // time, and the time between inference requests is very small (typically
      // less than a millisecond).
      // 
      // With this in mind, the inference server accumulates RemoteInference
      // requests into a single batch until one of the following occurs:
      //  1) It has accumulated one RemoteInference request from event client.
      //  2) The current batch has grown large enough that we won't be able to
      //     fit another max_game_batch_size_ inferences.
      //
      // Since a client can terminate (e.g. when a game is complete) while the
      // inference server is in the middle of processing a GetFeatures request,
      // we repeatedly pop with a timeout to allow us to periodically check the
      // current number of clients. Client terminations are rare, so it doesn't
      // really matter if we hold up one inference batch for a few tens of
      // milliseconds occasionally.
      auto timeout = absl::Milliseconds(50);
      size_t n = 0;
      RemoteInference game_batch;
      while (game_batches.size() < num_clients_ &&
             n + max_game_batch_size_ <= inference_batch_size_) {
        if (request_queue_.PopWithTimeout(&game_batch, timeout)) {
          game_batches.push_back(game_batch);
          n += game_batch.features.size();
        } else if (context->IsCancelled()) {
          return Status(StatusCode::CANCELLED, "connection terminated");
        }
      }
    }

    std::string byte_features(
        inference_batch_size_ * DualNet::kNumBoardFeatures, 0);
    size_t i = 0;
    for (const auto& game_batch : game_batches) {
      for (const auto& features : game_batch.features) {
        for (float f : features) {
          byte_features[i++] = f != 0 ? 1 : 0;
        }
      }
    }
    response->set_batch_id(batch_id_++);
    response->set_byte_features(std::move(byte_features));

    {
      absl::MutexLock lock(&pending_inferences_mutex_);
      pending_inferences_[response->batch_id()] = std::move(game_batches);
    }

    // std::cerr << absl::Now() << " DONE  GetFeatures\n";

    return Status::OK;
  }

  Status PutOutputs(ServerContext* context, const PutOutputsRequest* request,
                    PutOutputsResponse* response) override {
    // std::cerr << absl::Now() << " START PutOutputs\n";
    std::vector<RemoteInference> game_batches;
    {
      // std::cerr << "### PutOutputs" << std::endl;
      absl::MutexLock lock(&pending_inferences_mutex_);
      auto it = pending_inferences_.find(request->batch_id());
      MG_CHECK(it != pending_inferences_.end());
      game_batches = std::move(it->second);
      pending_inferences_.erase(it);
    }

    // Check we got the expected number of values.
    // (Note that if the prior GetFeatures response was padded, we may have
    // more values than batch_.size()).
    MG_CHECK(request->value().size() == static_cast<int>(inference_batch_size_))
        << "Expected " << inference_batch_size_ << " values, got "
        << request->value().size();

    // There should be kNumMoves policy values for each inference.
    MG_CHECK(request->policy().size() ==
             static_cast<int>(inference_batch_size_ * kNumMoves));

    size_t src_policy_idx = 0;
    for (auto& game_batch : game_batches) {
      for (size_t j = 0; j < game_batch.outputs.size(); ++j) {
        auto& dst_policy = game_batch.outputs[j].policy;
        for (int i = 0; i < kNumMoves; ++i) {
          dst_policy[i] = request->policy(src_policy_idx++);
        }
        game_batch.outputs[j].value = request->value(j);
      }
      game_batch.notification->Notify();
    }

    // std::cerr << absl::Now() << " DONE  PutOutputs\n";

    return Status::OK;
  }

 private:
  // Guaranteed maximum batch size that each client will send.
  const size_t max_game_batch_size_;

  // Target size of the batch sent in response to each GetFeaturesRequest.
  const size_t inference_batch_size_;

  std::atomic<int32_t> batch_id_{1};
  std::atomic<size_t> num_clients_{0};

  // After successfully popping the first request off request_queue, GetFeatures
  // will wait for up to the batch_timeout_ for more inference requests before
  // replying.
  absl::Duration batch_timeout_;

  ThreadSafeQueue<RemoteInference> request_queue_;

  // Mutex that is locked while popping inference requests off request_queue_
  // (see GetFeatures() for why this is needed).
  absl::Mutex get_features_mutex_;

  // Mutex that protects access to pending_inferences_.
  absl::Mutex pending_inferences_mutex_;

  // Map from batch ID to list of remote inference requests in that batch.
  std::map<int32_t, std::vector<RemoteInference>> pending_inferences_
      GUARDED_BY(&pending_inferences_mutex_);

  friend class InferenceClient;
};

class InferenceClient : public DualNet {
 public:
  explicit InferenceClient(InferenceServiceImpl* service) : service_(service) {
    service_->num_clients_++;
  }

  ~InferenceClient() {
    service_->num_clients_--;
  }

  void RunMany(absl::Span<const BoardFeatures> features,
               absl::Span<Output> outputs) override {
    MG_CHECK(features.size() <= service_->max_game_batch_size_);

    // std::cerr << absl::StrCat("### RunMany ", features.size(), "\n");
    absl::Notification notification;
    service_->request_queue_.Push({features, outputs, &notification});
    notification.WaitForNotification();
  }

 private:
  InferenceServiceImpl* service_;
  size_t max_batch_size_;
};

}  // namespace internal

InferenceServer::InferenceServer(
    int max_game_batch_size, int inference_batch_size, int port) {
  auto server_address = absl::StrCat("0.0.0.0:", port);
  service_ = absl::make_unique<internal::InferenceServiceImpl>(
      max_game_batch_size, inference_batch_size);

  ServerBuilder builder;
  builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
  builder.RegisterService(service_.get());
  server_ = builder.BuildAndStart();
  std::cerr << "Inference server listening on port " << port << std::endl;

  thread_ = std::thread([this]() { server_->Wait(); });
}

InferenceServer::~InferenceServer() {
  // Passing gpr_inf_past to Shutdown makes it shutdown immediately.
  server_->Shutdown(gpr_inf_past(GPR_CLOCK_REALTIME));
  thread_.join();
}

std::unique_ptr<DualNet> InferenceServer::NewDualNet() {
  return absl::make_unique<internal::InferenceClient>(service_.get());
}

}  // namespace minigo
