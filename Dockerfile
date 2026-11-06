# Etapas: base (dependencias y código), tests (agrega lo que las pruebas leen) y app.
# `app` va al final porque es la que se construye por omisión, como en Render.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
RUN useradd --create-home --uid 1000 autofix
COPY pyproject.toml ./
# Las dependencias se leen de pyproject.toml y se instalan antes de copiar el código: así un
# cambio en src/ no las reinstala. El código se importa por PYTHONPATH, no como paquete.
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']))" > /tmp/dependencias.txt \
    && pip install --no-cache-dir -r /tmp/dependencias.txt
COPY src ./src

FROM base AS tests
RUN python -c "import tomllib; print('\n'.join(tomllib.load(open('pyproject.toml', 'rb'))['project']['optional-dependencies']['dev']))" > /tmp/dev.txt \
    && pip install --no-cache-dir -r /tmp/dev.txt
COPY tests ./tests
COPY docs ./docs
COPY database ./database
COPY datos ./datos
COPY reportes ./reportes
# Las pruebas escriben reportes/ y .coverage.
RUN chown -R autofix:autofix /app
USER autofix
CMD ["pytest", "--cov=src", "--cov-branch", "--cov-report=term-missing", "--cov-fail-under=80"]

FROM base AS app
USER autofix
EXPOSE 8000
# Con `sh -c` se expande PORT (Render lo define); `exec` deja a uvicorn recibir las señales de apagado.
CMD ["sh", "-c", "exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
