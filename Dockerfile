FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies, FFmpeg, curl, git, nodejs and npm
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    git \
    nodejs \
    npm \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Deno for JS Challenge Execution
RUN curl -fsSL https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip -o /tmp/deno.zip \
    && unzip /tmp/deno.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/deno \
    && rm -f /tmp/deno.zip

# Clone and build bgutil PO Token Provider (v1.3.2)
WORKDIR /opt
RUN git clone --depth 1 --branch 1.3.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git bgutil-ytdlp-pot-provider

WORKDIR /opt/bgutil-ytdlp-pot-provider/server
RUN npm ci && npx tsc

# Install only the fast HTTP provider plugin
RUN mkdir -p /root/yt-dlp-plugins/bgutil-ytdlp-pot-provider \
    && cp -r /opt/bgutil-ytdlp-pot-provider/plugin/* /root/yt-dlp-plugins/bgutil-ytdlp-pot-provider/ \
    && mkdir -p /etc/yt-dlp/plugins/bgutil-ytdlp-pot-provider \
    && cp -r /opt/bgutil-ytdlp-pot-provider/plugin/* /etc/yt-dlp/plugins/bgutil-ytdlp-pot-provider/ \
    && find /root/yt-dlp-plugins /etc/yt-dlp/plugins -name "*script*.py" -delete

# Configure plugin directories for yt-dlp
RUN mkdir -p /root/.config/yt-dlp \
    && printf '%s\n' '--plugin-dirs' '/root/yt-dlp-plugins' > /root/.config/yt-dlp/config \
    && mkdir -p /etc/yt-dlp \
    && printf '%s\n' '--plugin-dirs' '/etc/yt-dlp/plugins' > /etc/yt-dlp/config

# Downly API Application
WORKDIR /app

ENV PORT=10000
ENV BGUTIL_PORT=4416
ENV FFMPEG_PATH=/usr/bin
ENV FFMPEG_LOCATION=/usr/bin
ENV STORAGE_DIR=/tmp/downly-storage

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 10000

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
