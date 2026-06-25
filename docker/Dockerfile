# Stage 1: install Python deps in isolation
FROM python:3.12-slim AS python-deps

WORKDIR /deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: runtime image with XeLaTeX + Python packages
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV RESUME_IN_DOCKER=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      texlive-xetex \
      texlive-latex-extra \
      texlive-fonts-recommended \
      fonts-lmodern \
      latexmk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=python-deps /usr/local/lib/python3.12/site-packages \
                         /usr/local/lib/python3.12/site-packages

WORKDIR /workspace

ENTRYPOINT ["bash", "build_all.sh"]
