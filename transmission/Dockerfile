# Use a base image with required build tools
FROM debian:bullseye-slim

# Install required build tools, dependencies, and Python
RUN apt-get update && \
    apt-get install -y \
    build-essential cmake pkg-config \
    libcurl4-openssl-dev libssl-dev libminiupnpc-dev \
    libevent-dev gettext libdb-dev \
    python3 python3-dev python3-distutils && \
    rm -rf /var/lib/apt/lists/*

# Copy the entire transmission source into container
COPY . ./Transmission/

WORKDIR /Transmission

# Build Transmission
RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build && \
    cmake --install build --prefix /usr/local && \
    rm -rf /Transmission

# Expose UI and torrent ports
EXPOSE 9091 51413

# Create config folder
RUN mkdir /config

# Entrypoint runs transmission-daemon with config directory
ENTRYPOINT ["/usr/local/bin/transmission-daemon", "-f", "--config-dir", "/config"]
