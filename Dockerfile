FROM python:3.12-slim

# System dependencies for cyvcf2 (C extension requiring htslib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gwas_variant_analyzer as editable package
COPY gwas_variant_analyzer/ ./gwas_variant_analyzer/
RUN pip install --no-cache-dir -e ./gwas_variant_analyzer

# Copy rest of the application
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
