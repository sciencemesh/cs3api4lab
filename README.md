# cs3api4lab

![Github Actions Status](https://github.com/sciencemesh/cs3api4lab/workflows/Build/badge.svg)

This is an Extension for Jupyterlab that allow the retrieval of files and and added functionality (i.e sharing) provided by the CS3APIs.

This extension is composed of a Python package named `cs3api4lab` and a NPM package named `cs3api4lab`
for the frontend extension.

The Python package implements the Jupyter `ContentsManager` and `Checkpoints` interfaces, and can be used to replace 
the default managers.


## Requirements

* JupyterLab >= 2.0

## Install

Note: You will need NodeJS to install the extension.

```bash
pip install cs3api4lab
jupyter serverextension enable --py cs3api4lab --sys-prefix
jupyter labextension install @sciencemesh/cs3api4lab
```

To enable the Manager and Chekpoints, the following configuration needs to be added to `jupyter_notebook_config.py`:

```python
c.NotebookApp.contents_manager_class = 'cs3api4lab.CS3APIsManager'
c.ContentsManager.checkpoints_class = 'cs3api4lab.CS3APIsCheckpoints'
```

## Contributing

### Install

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Move to cs3api4lab directory

# Install the contents manager
pip install -e .
# Register server extension
jupyter serverextension enable --py cs3api4lab --sys-prefix

# Install dependencies
jlpm
# Build Typescript source
jlpm build
# Link your development version of the extension with JupyterLab
jupyter labextension install .
# Rebuild Typescript source after making changes
jlpm build
# Rebuild JupyterLab after making any changes
jupyter lab build
```

You can watch the source directory and run JupyterLab in watch mode to watch for changes in the extension's source and automatically rebuild the extension and application.

```bash
# Watch the source directory in another terminal tab
jlpm watch
# Run jupyterlab in watch mode in one terminal tab
jupyter lab --watch
```

Now every change will be built locally and bundled into JupyterLab. Be sure to refresh your browser page after saving file changes to reload the extension (note: you'll need to wait for webpack to finish, which can take 10s+ at times).

### Uninstall

```bash
pip uninstall cs3api4lab
jupyter labextension uninstall @sciencemesh/cs3api4lab
```

### Setup env for integration testing

#### Create local IOP instance 
Follow the first 3 steps from this tutorial https://reva.link/docs/tutorials/share-tutorial/
or create with commands: 

```bash
git clone https://github.com/cs3org/reva
cd reva
make deps
make
cd examples/ocmd/ && mkdir -p /tmp/reva && && mkdir -p /var/tmp/reva 
```

#### Run test

Goto test folder:
```bash
cd cs3api4lab/tests
```

Run cs3 API connector test:
```bash
python test_cs3_file_api.py
python test_cs3apismanager.py
```

### Setup env 

Create config:
```
jupyter notebook --generate-config
```

Enable CS3 File Content Manager
Replace in file HOME_FOLDER/.jupyter/jupyter_notebook_config.py line 

```
c.NotebookApp.contents_manager_class = 'notebook.services.contents.largefilemanager.LargeFileManager'
```

to

```
c.NotebookApp.contents_manager_class = 'cs3api4lab.CS3APIsManager'
```

### CS3 config file
Copy cs3 example config file from "jupyter-config/jupyter_cs3_config.json"
to:
* Windows: 
```C:\Users\{USER_PROFILE}\.jupyter\```
* Linux:
 ```HOME_FOLDER/.jupyter/```

## Setup for docker image

### Build docker image from local source code

Clone repo and switch to “docker” branch 
```bash
git clone https://github.com/JarCz/cs3api4lab.git
cd cs3api4lab
git switch docker
```

Modify the configuration file, set reva host, user authorization data, etc in file: jupyter-config/jupyter_cs3_config.json

```bash
nano jupyter-config/jupyter_cs3_config.json
```
Build docker image:
```bash
docker build -t cs3api4lab .
```

Run docker image:
```bash
docker run -p 8888:8888 cs3api4lab
```

Run docker image with overwriting config variables:

- all supported value:
```bash
docker run -p 8888:8888 -e CS3_REVAHOST=IP:PORT -e CS3_CLIENT_ID=user_id -e CS3_CLIENT_SECRET=user_pass -e CS3_HOME_DIR="/test" cs3api4lab
```

- user authorization data:
```bash
docker run -p 8888:8888 -e CS3_CLIENT_ID=user_id -e CS3_CLIENT_SECRET=user_pass cs3api4lab
```

### Quick build
```bash
pip install -e .
jupyter serverextension enable --py cs3api4lab --sys-prefix
jlpm
jlpm build
jupyter labextension install .
jlpm build
jupyter lab build
jupyter lab 

```

### Quick build python
```bash
jupyter labextension install .
jupyter lab
```