FROM jupyter/base-notebook:lab-3.2.9

USER root

COPY dist /opt/cs3/

# This image contains a newer version of jupyterlab, so our extension will downgrade it
RUN cd /opt/cs3 && \
    pip install --no-cache-dir cs3api4lab*.tar.gz && \
    cd / && \
    rm -rf /opt/cs3 && \
    fix-permissions "/home/${NB_USER}"

RUN echo "c.ServerApp.contents_manager_class = 'cs3api4lab.CS3APIsManager'" >> /etc/jupyter/jupyter_server_config.py
RUN jupyter labextension disable @jupyterlab/filebrowser-extension
RUN jupyter labextension disable @jupyterlab/filebrowser

USER $NB_UID

EXPOSE 8888
