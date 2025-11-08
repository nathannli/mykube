# Build stage
FROM debian:bullseye-slim AS builder

RUN apt-get update && apt-get install -y \
    build-essential cmake pkg-config libcurl4-openssl-dev libssl-dev libminiupnpc-dev \
    libevent-dev gettext libdb-dev python3 python3-dev python3-distutils && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /transmission
COPY . .

RUN cmake -B build -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build && \
    cmake --install build --prefix /usr/local

# Runtime stage
FROM debian:bullseye-slim

# Install minimal runtime dependencies for transmission-daemon
RUN apt-get update && apt-get install -y \
    libcurl4 openssl libminiupnpc17 libevent-2.1-7 dbus && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

RUN mkdir /config

EXPOSE 9091 51413

ENTRYPOINT ["/usr/local/bin/transmission-daemon", "-f", "--config-dir", "/config"]
