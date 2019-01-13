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

#include "cc/platform/utils.h"

#include <sys/sysctl.h>
#include <unistd.h>
#include <cstring>

#include "cc/logging.h"

namespace minigo {

bool FdSupportsAnsiColors(int fd) { return isatty(fd); }

int GetNumLogicalCpus() {
  int nproc = 0;
  size_t len;
  MG_CHECK(sysctlbyname("hw.logicalcpu", &nproc, &len, nullptr, 0) == 0);
  MG_CHECK(len == sizeof(nproc));
  return nproc;
}

std::string GetHostname() {
  char hostname[256];
  if (gethostname(hostname, sizeof(hostname)) != 0) {
    std::strncpy(hostname, "unknown", sizeof(hostname));
  }
  return std::string(hostname);
}

}  // namespace minigo
