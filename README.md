# cs3api4lab

[![Github Actions Status](https://github.com/sciencemesh/cs3api4lab.git/workflows/Build/badge.svg)](https://github.com/sciencemesh/cs3api4lab.git/actions/workflows/build.yml)

This is an Extension for Jupyterlab that allow the retrieval of files and and added functionality (i.e sharing) provided by the CS3APIs.


This extension is composed of a Python package named `cs3api4lab`
for the server extension and a NPM package named `cs3api4lab`
for the frontend extension.

The Python package implements the Jupyter `ContentsManager` and `Checkpoints` interfaces, and can be used to replace 
the default managers.


## Requirements

* JupyterLab >= 3.0

## Install

To install the extension, execute:

```bash
pip install cs3api4lab
```

## Uninstall

To remove the extension, execute:

```bash
pip uninstall cs3api4lab
```


## Troubleshoot

If you are seeing the frontend extension, but it is not working, check
that the server extension is enabled:

```bash
jupyter server extension list
```

If the server extension is installed and enabled, but you are not seeing
the frontend extension, check the frontend extension is installed:

```bash
jupyter labextension list
```


## Contributing

### Development install

Note: You will need NodeJS to build the extension package.

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Change directory to the cs3api4lab directory
# Install package in development mode
pip install -e .
# Link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite
# Server extension must be manually installed in develop mode
jupyter server extension enable cs3api4lab
# Rebuild extension Typescript source after making changes
jlpm run build
```

You can watch the source directory and run JupyterLab at the same time in different terminals to watch for changes in the extension's source and automatically rebuild the extension.

```bash
# Watch the source directory in one terminal, automatically rebuilding when needed
jlpm run watch
# Run JupyterLab in another terminal
jupyter lab
```

With the watch command running, every saved change will immediately be built locally and available in your running JupyterLab. Refresh JupyterLab to load the change in your browser (you may need to wait several seconds for the extension to be rebuilt).

By default, the `jlpm run build` command generates the source maps for this extension to make it easier to debug using the browser dev tools. To also generate source maps for the JupyterLab core extensions, you can run the following command:

```bash
jupyter lab build --minimize=False
```



### Development uninstall

```bash
# Server extension must be manually disabled in develop mode
jupyter server extension disable cs3api4lab
pip uninstall cs3api4lab
```

In development mode, you will also need to remove the symlink created by `jupyter labextension develop`
command. To find its location, you can run `jupyter labextension list` to figure out where the `labextensions`
folder is located. Then you can remove the symlink named `cs3api4lab` within that folder.


### Setup env for integration testing

#### Create local IOP instance 
Follow the first 3 steps from this tutorial https://reva.link/docs/tutorials/share-tutorial/
or create with commands: 

```bash
git clone https://github.com/cs3org/reva
cd reva
make deps
make
mkdir -p /var/tmp/reva
cd examples/ocmd/
../../cmd/revad/revad -c ocmd-server-1.toml
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
jupyter server --generate-config
```

Enable CS3 File Content Manager
Replace in file HOME_FOLDER/.jupyter/jupyter_server_config.py line 

```
c.ServerApp.contents_manager_class = 'notebook.services.contents.largefilemanager.LargeFileManager'
```

to

```
c.ServerApp.contents_manager_class = 'cs3api4lab.CS3APIsManager'
```
### Disable default file browser
To disable the default file browser use these commands in the console:
```bash
jupyter labextension disable @jupyterlab/filebrowser-extension
jupyter labextension disable @jupyterlab/filebrowser
```
You can also use a config file to disable the default file browser, copy page_config.json from jupyter-config/page_config.json to:
* Windows:
  ```C:\Users\{USER_PROFILE}\.jupyter\labconfig```
* Linux:
  ```HOME_FOLDER/.jupyter/labconfig```

### CS3 config file
Copy cs3 example config file from "jupyter-config/jupyter_cs3_config.json"
to:
* Windows: 
```C:\Users\{USER_PROFILE}\.jupyter\```
* Linux:
 ```HOME_FOLDER/.jupyter/```

Config file fields:
- revahost - address and port on which the Reva server is listening
- auth_token_validity - the lifetime of the authenticating token
- endpoint - endpoint for Reva storage provider
- chunk_size - size of the downloaded fragment from Reva
- secure_channel - secure channel flag
- client_cert - public key file path (PEM-encoded)
- client_key - private key file path
- ca_cert - certificate authority file path
- client_id - client login to authenticate in Reva
- client_secret - client password to authenticate in Reva
- root_dir_list - list of root dirs, for example https://developer.sciencemesh.io/docs/iop/deployment/kubernetes/providers/ root dirs are "/home,/reva"

#### Examples of different authentication methods:

If you want to use a different authentication method replace the "authenticator_class" in the config file 
and put necessary config values for authenticator class.  

  * Reva user and secret:
 ```json
{
  "cs3":{
    ...
	"authenticator_class": "cs3api4lab.auth.RevaPassword",
	"client_id": "einstein",
	"client_secret": "relativity"
	}
}
```
  * Oauth token from config value
 ```json
{
  "cs3":{
    ...
	"authenticator_class": "cs3api4lab.auth.Oauth",
	"oauth_token":"OUATH TOKEN",
	"client_id": "einstein"
	}
}
```
  * Oauth token from file
 ```json
{
  "cs3":{
    ...
	"authenticator_class": "cs3api4lab.auth.Oauth",
	"oauth_token":"PATH TO FILE",
	"client_id": "einstein"
	}
}
```
  * Eos token from config value
 ```json
{
  "cs3":{
    ...
	"authenticator_class": "cs3api4lab.auth.Eos",
	"eos_token":"oauth2:<OAUTH_TOKEN>:<OAUTH_INSPECTION_ENDPOINT>",
	"client_id": "einstein"
	}
}
```
  * Eos token from file
 ```json
{
  "cs3":{
    ...
	"authenticator_class": "cs3api4lab.auth.Eos",
	"eos_file":"PATH TO FILE",
	"client_id": "einstein"
	}
}
```

## Setup for docker image

### Build docker image from local source code

Clone the repo: 
```bash
git clone https://github.com/sciencemesh/cs3api4lab.git
cd cs3api4lab
```
Build docker image:
```bash
docker build -t cs3api4lab .
```
Available environmental variables:
```
- CS3_REVA_HOST - address and port on which the Reva server is listening [required]
- CS3_CLIENT_ID - client login to authenticate in Reva [required]
- CS3_CLIENT_SECRET - client password to authenticate in Reva [required in case of basic login]
- CS3_AUTH_TOKEN_VALIDITY - the lifetime of the authenticating token
- CS3_ENDPOINT - endpoint for Reva storage provider
- CS3_HOME_DIR - home directory of the user
- CS3_CHUNK_SIZE - size of the downloaded fragment from Reva
- CS3_SECURE_CHANNEL - secure channel flag
- CS3_CLIENT_CERT - public key file path (PEM-encoded)
- CS3_CLIENT_KEY - private key file path
- CS3_CA_CERT - certificate authority file path
- CS3_LOGIN_TYPE - Reva login type
- CS3_AUTHENTICATOR_CLASS - class of the authentication provider
- CS3_ROOT_DIR_LIST - list of root containers
```
Run docker image providing necessary variables:
```bash
docker run -p 8888:8888 -e CS3_CLIENT_ID=einstein -e CS3_CLIENT_SECRET=relativity -e CS3_REVA_HOST=localhost:19000 cs3api4lab
```
Run docker image after overwriting the config variables explicitly or in the reva_config.env:
```bash
docker run -p 8888:8888 --env-file reva_config.env cs3api4lab
```
