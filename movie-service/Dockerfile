# movie-service/Dockerfile

# Utiliser l'image python 3.8 slim comme image de base
FROM python:3.8-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt dans le répertoire de travail
COPY ./requirements.txt /app/requirements.txt

# Installer les dépendances système (gcc) nécessaires à l'installation des paquets Python
RUN apt-get update && apt-get install -y gcc curl && \
    apt-get clean

# Installer les dépendances Python à partir de requirements.txt
RUN pip install -r /app/requirements.txt \
&& rm -rf /root/.cache/pip

# Copier le reste de l'application dans le répertoire de travail
COPY . /app/

# Ajouter les bonnes permissions pour les fichiers dans /app
RUN chmod -R 755 /app  

# Ajouter la commande par défaut pour démarrer l'application avec uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]