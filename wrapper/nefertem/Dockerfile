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
RUN rm $DHUB_VERSION.zip

# Install digitalhub-core, neferetem
RUN pip install digitalhub-sdk/core
RUN pip install digitalhub-sdk/data --no-deps
RUN pip install digitalhub-sdk/ --no-deps
RUN pip install digitalhub-sdk/data/modules/nefertem[local]

# Get nefertem
ARG NEFERTEM_VERSION=2.0.5
RUN wget https://github.com/scc-digitalhub/nefertem/archive/refs/tags/$NEFERTEM_VERSION.zip
RUN unzip $NEFERTEM_VERSION.zip
RUN mv nefertem-$NEFERTEM_VERSION nefertem
RUN rm $NEFERTEM_VERSION.zip

# Install nefertem plugins
RUN pip install ./nefertem/plugins/frictionless*
RUN pip install ./nefertem/plugins/duckdb*
RUN pip install ./nefertem/plugins/sqlalchemy*
RUN pip install ./nefertem/plugins/ydata*

# Copy wrapper and set entry point
COPY wrapper.py /app/

# Cleanup folders
RUN rm -rf digitalhub-sdk nefertem

ENTRYPOINT ["python", "wrapper.py"]
