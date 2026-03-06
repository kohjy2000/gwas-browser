FROM python:3.12-slim

# Minimal runtime libraries only (cyvcf2 wheel bundles htslib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gwas_variant_analyzer package
COPY gwas_variant_analyzer/ ./gwas_variant_analyzer/
RUN pip install --no-cache-dir -e ./gwas_variant_analyzer

# Copy application and data
COPY gwas_dashboard_package/ ./gwas_dashboard_package/
COPY data/ ./data/

# Environment
ENV RENDER=true
ENV GWAS_REMOTE_SEARCH=1
ENV GWAS_TRAIT_LIST_AUTOBOOTSTRAP=0

EXPOSE 10000

CMD ["gunicorn", \
     "--bind", "0.0.0.0:10000", \
     "--workers", "1", \
     "--threads", "2", \
     "--timeout", "120", \
     "gwas_dashboard_package.src.main:app"]
