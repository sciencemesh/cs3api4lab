import json
import nest_asyncio

from pathlib import Path

from .handlers import setup_handlers
from ._version import __version__

from cs3api4lab.api.cs3apismanager import CS3APIsManager

HERE = Path(__file__).parent.resolve()

with (HERE / "labextension" / "package.json").open() as fid:
    data = json.load(fid)


def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": data["name"]}]


def _jupyter_server_extension_points():
    return [{"module": "cs3api4lab"}]


def _load_jupyter_server_extension(server_app):
    """Registers the API handler to receive HTTP requests from the frontend extension.
    Parameters
    ----------
    server_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """

    #line below must be run in order for loop.run_until_complete() to work
    nest_asyncio.apply()

    url_path = "cs3api4lab"
    setup_handlers(server_app.web_app, url_path)
    server_app.log.info(
        f"Registered cs3api4lab extension at URL path /{url_path}"
    )

# For backward compatibility with the classical notebook
load_jupyter_server_extension = _load_jupyter_server_extension
