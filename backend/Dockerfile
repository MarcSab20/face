FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système pour WeasyPrint et autres
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    # Dépendances pour WeasyPrint
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libcairo2-dev \
    libgobject-2.0-0 \
    libglib2.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    shared-mime-info \
    # Polices et outils supplémentaires
    fonts-liberation \
    fonts-dejavu-core \
    fontconfig \
    # Dépendances supplémentaires pour WeasyPrint
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install -r requirements.txt --use-deprecated=legacy-resolver

# Copier le code de l'application
COPY app/ ./app/

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]