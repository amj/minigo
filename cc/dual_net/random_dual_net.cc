// Copyright 2019 Google LLC
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

#include "cc/dual_net/random_dual_net.h"

#include <cmath>
#include <vector>

#include "absl/memory/memory.h"
#include "absl/strings/numbers.h"
#include "absl/strings/str_cat.h"
#include "absl/strings/str_split.h"
#include "cc/logging.h"
#include "cc/model/buffered_model.h"
#include "cc/platform/utils.h"

namespace minigo {

RandomDualNet::RandomDualNet(std::string name,
                             const FeatureDescriptor& feature_desc,
                             uint64_t seed, float policy_stddev,
                             float value_stddev)
    : Model(std::move(name), feature_desc, 1),
      rnd_(seed, Random::kUniqueStream),
      policy_stddev_(policy_stddev),
      value_stddev_(value_stddev) {}

void RandomDualNet::RunMany(const std::vector<const ModelInput*>& inputs,
                            std::vector<ModelOutput*>* outputs,
                            std::string* model_name) {
  for (auto* output : *outputs) {
    rnd_.NormalDistribution(0.5, policy_stddev_, &output->policy);
    for (auto& p : output->policy) {
      p = std::exp(p);
    }
    float sum = 0;
    for (auto p : output->policy) {
      sum += p;
    }
    for (auto& p : output->policy) {
      p /= sum;
    }

    do {
      output->value = rnd_.NormalDistribution(0, value_stddev_);
    } while (output->value < -1 || output->value > 1);
  }
  if (model_name != nullptr) {
    *model_name = name();
  }
}

RandomDualNetFactory::RandomDualNetFactory(uint64_t seed) : seed_(seed) {}

std::unique_ptr<Model> RandomDualNetFactory::NewModel(
    const std::string& descriptor) {
  std::vector<absl::string_view> parts = absl::StrSplit(descriptor, ':');
  MG_CHECK(parts.size() == 3);

  FeatureDescriptor feature_desc;
  float policy_stddev, value_stddev;
  if (parts[0] == "agz") {
    feature_desc = FeatureDescriptor::Create<AgzFeatures>();
  } else if (parts[0] == "extra") {
    feature_desc = FeatureDescriptor::Create<ExtraFeatures>();
  } else {
    MG_LOG(FATAL) << "unrecognized feature type \"" << parts[0] << "\"";
    return nullptr;
  }
  MG_CHECK(absl::SimpleAtof(parts[1], &policy_stddev));
  MG_CHECK(absl::SimpleAtof(parts[2], &value_stddev));

  int num_cpus = GetNumLogicalCpus();
  auto qualified_descriptor = absl::StrCat("rnd:", descriptor);
  std::vector<std::unique_ptr<Model>> models;
  for (int i = 0; i < num_cpus; ++i) {
    models.push_back(
        absl::make_unique<RandomDualNet>(qualified_descriptor, feature_desc,
                                         seed_, policy_stddev, value_stddev));
  }

  return absl::make_unique<BufferedModel>(std::move(models));
}

}  // namespace minigo
