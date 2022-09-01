FROM jupyter/base-notebook:lab-3.2.9

USER root

COPY . /opt/cs3/

# This image contains a newer version of jupyterlab, so our extension will downgrade it
# On the other hand, we have newer dependencies (i.e node), making it easier to install
RUN cd /opt/cs3 && \
    pip install --no-cache-dir . && \
    jupyter lab clean && \
    rm -rf "/home/${NB_USER}/.cache/yarn" && \
    cd / && \
    rm -rf /opt/cs3 && \
    fix-permissions "/home/${NB_USER}"

RUN echo "c.ServerApp.contents_manager_class = 'cs3api4lab.CS3APIsManager'" >> /etc/jupyter/jupyter_server_config.py

RUN jupyter labextension disable @jupyterlab/filebrowser-extension:browser

USER $NB_UID

EXPOSE 8888
