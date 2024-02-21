FROM python:3.9

# Repo info
LABEL org.opencontainers.image.source=https://github.com/scc-digitalhub/digitalhub-core

# Set working dir
WORKDIR /app/

# Get digitalhub-sdk
ARG DHUB_VERSION=
RUN echo $DHUB_VERSION
RUN wget https://github.com/scc-digitalhub/digitalhub-sdk/archive/refs/tags/$DHUB_VERSION.zip
RUN unzip $DHUB_VERSION.zip
RUN mv digitalhub-sdk-$DHUB_VERSION digitalhub-sdk

# Install digitalhub-core, dbt
RUN pip install ./digitalhub-sdk/core
RUN pip install ./digitalhub-sdk/data --no-deps
RUN pip install ./digitalhub-sdk/data/modules/dbt --no-deps
RUN pip install ./digitalhub-sdk --no-deps
# module[local] will break, dbt has pYaml > 6, digitalhub ~5, because of mlrun-kfp
# Pandas < 2.2 because of sqlalchemy 1.4 for mlrun
RUN pip install dbt-postgres==1.6.7 pandas==2.1.4

# Copy wrapper and set entry point
COPY wrapper.py /app/

# Cleanup
RUN rm -rf digitalhub-sdk $DHUB_VERSION.zip

ENTRYPOINT ["python", "wrapper.py"]
