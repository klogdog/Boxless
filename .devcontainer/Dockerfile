FROM mcr.microsoft.com/devcontainers/javascript-node:20

# Python and Poetry are installed via devcontainer features configured in devcontainer.json

# Install Docker CLI and daemon
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli docker-ce

# Create Docker daemon directory
RUN mkdir -p /var/lib/docker

# Set up Docker daemon to start on container startup
RUN echo '#!/bin/bash\n\
# Start Docker daemon\n\
dockerd --host=unix:///var/run/docker.sock --host=tcp://0.0.0.0:2376 --tls=false --iptables=false --bridge=none &\n\
\n\
# Wait for Docker to be ready\n\
echo "Waiting for Docker daemon to start..."\n\
while ! docker info >/dev/null 2>&1; do\n\
    sleep 1\n\
done\n\
echo "Docker daemon is ready!"\n\
\n\
# Execute the original command\n\
exec "$@"' > /usr/local/bin/start-docker.sh \
    && chmod +x /usr/local/bin/start-docker.sh

# Set the startup script as entrypoint
ENTRYPOINT ["/usr/local/bin/start-docker.sh"]
