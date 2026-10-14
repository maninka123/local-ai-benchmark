FROM mcr.microsoft.com/playwright:v1.58.2-noble
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/python
ENV PATH="/opt/python/bin:${PATH}"
RUN pip install --no-cache-dir pandas==2.3.3 numpy==2.2.6 matplotlib==3.10.9 plotly==7.1.0 pillow==12.3.0
WORKDIR /opt/lab
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts
COPY browser_probe.mjs ./browser_probe.mjs
COPY viewer_server.py ./viewer_server.py
RUN mkdir /input /output && chown -R 1000:1000 /input /output
ENV NODE_PATH=/opt/lab/node_modules
USER 1000:1000
WORKDIR /output
