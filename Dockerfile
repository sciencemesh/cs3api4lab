FROM jupyter/base-notebook:a07573d685a4
# Built from... https://hub.docker.com/r/jupyter/base-notebook/
#               https://github.com/jupyter/docker-stacks/blob/master/base-notebook/Dockerfile

COPY cs3api4lab /opt/cs3/cs3api4lab
COPY src /opt/cs3/src
COPY style /opt/cs3/style
COPY jupyter-config/cs3api4lab.json /opt/cs3/jupyter-config/cs3api4lab.json
COPY setup.py /opt/cs3/setup.py
COPY README.md /opt/cs3/README.md
COPY package.json /opt/cs3/package.json
COPY package-lock.json /opt/cs3/package-lock.json
COPY yarn.lock /opt/cs3/yarn.lock
COPY tsconfig.json /opt/cs3/tsconfig.json
COPY pyproject.toml /opt/cs3/pyproject.toml

USER root

RUN cd /opt/cs3 && \
	python -m pip install --upgrade pip && \
	pip install --no-cache-dir jupyter_packaging && \
	pip install --no-cache-dir -e . && \
	jupyter serverextension enable --py cs3api4lab --sys-prefix && \
	jlpm && \
	jlpm build && \
	jupyter labextension install . && \
	jlpm build && \
    jupyter lab build -y && \
    jupyter lab clean -y && \
	npm cache clean --force && \
    rm -rf "/home/${NB_USER}/.cache/yarn" && \
    rm -rf "/home/${NB_USER}/.node-gyp" && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/opt/cs3" && \
    fix-permissions "/home/${NB_USER}" && \
	sed -i 's/#c.NotebookApp.contents_manager_class/c.NotebookApp.contents_manager_class/g' /home/${NB_USER}/.jupyter/jupyter_notebook_config.py && \
	sed -i 's/notebook.services.contents.largefilemanager.LargeFileManager/cs3api4lab.CS3APIsManager/g' /home/${NB_USER}/.jupyter/jupyter_notebook_config.py

#
# Copy cs3Api plugin config
#	
COPY jupyter-config/jupyter_cs3_config.json /home/${NB_USER}/.jupyter/jupyter_cs3_config.json
RUN fix-permissions "/home/${NB_USER}"
	
EXPOSE 8888

ENTRYPOINT ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root", "--no-browser"]
	
USER $NB_UID

WORKDIR $HOME

