FROM postgres:16

RUN apt-get update \
    && apt-get install -y postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*

ENV POSTGRES_DB=geo_rag \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=postgres

COPY docker/init-vector.sql /docker-entrypoint-initdb.d/10-init-vector.sql

EXPOSE 5432
