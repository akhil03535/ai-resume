FROM python:3.12-slim

WORKDIR /app

# System deps: libpq for psycopg2, plus WeasyPrint's rendering dependencies.
# NOTE: Debian Trixie (the base of python:3.12-slim) renamed
# libgdk-pixbuf2.0-0 -> libgdk-pixbuf-2.0-0 and dropped the old transitional
# package name entirely - using the old name here fails the build with
# "Package libgdk-pixbuf2.0-0 has no installation candidate".
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libcairo2 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# PyTorch's default Linux wheel on PyPI declares nvidia-cublas-cu12,
# nvidia-cudnn-cu12, nvidia-cusparselt-cu12, etc. as dependencies (the CUDA
# build) - hundreds of MB to multiple GB, and what caused prior build
# timeouts. PyTorch's own CPU-only index (download.pytorch.org/whl/cpu) does
# NOT declare those - installing from it FIRST means sentence-transformers
# (installed next, from requirements.txt) finds torch already satisfied and
# never falls back to PyPI's default CUDA wheel.
# A version range (not an exact patch pin) is used deliberately: this
# sandbox cannot reach download.pytorch.org to confirm any single patch
# version is published for linux/py3.12 on that index, so an overly strict
# pin risks a hard "no matching distribution" failure that can't be verified
# here. Constrained to the 2.4.x/2.5.x line, which sentence-transformers
# 3.1.1 (requires torch>=1.11) is well within.
RUN pip install --no-cache-dir "torch>=2.4.0,<2.6.0" --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
