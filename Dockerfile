ARG BUILD_FROM
FROM $BUILD_FROM

# Installer Python
RUN apk add --no-cache python3 py3-pip

# Créer un virtualenv (solution PEP668)
RUN python3 -m venv /opt/venv

# Activer venv dans PATH
ENV PATH="/opt/venv/bin:$PATH"

# Installer dépendances Python
RUN pip install --no-cache-dir bottle paste

WORKDIR /app

COPY image-viewer.py .
COPY run.sh .

RUN chmod a+x /app/run.sh

CMD [ "/app/run.sh" ]
