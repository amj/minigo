FROM nvidia/opencl:devel-ubuntu18.04

# Install build depedencies
RUN apt update && apt-get install -y \
        build-essential \
        curl \
  git \
  clinfo \
  cmake \
  libboost-dev \
  libboost-program-options-dev \
  libboost-filesystem-dev \
  opencl-headers \
  ocl-icd-libopencl1 \
  ocl-icd-opencl-dev \
  python-pip \
  virtualenv \
  wget \
  zlib1g-dev

WORKDIR /
RUN virtualenv -p /usr/bin/python2 mg_venv
RUN . mg_venv/bin/activate \
  && pip install gomill
# ringmaster now available at /mg_venv/bin/ringmaster

WORKDIR /app

# Clone github repo
RUN git clone https://github.com/gcp/leela-zero \
  && cd leela-zero \
  && git submodule update --init --recursive

WORKDIR leela-zero
RUN mkdir build && cd build \
  && cmake .. \
  && cmake --build . -- -j4

RUN wget -q https://zero.sjeng.org/best-network

run ls






