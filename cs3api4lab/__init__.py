from notebook.utils import url_path_join

from ._version import __version__ 
from .cs3apischeckpoint import CS3APIsCheckpoints
from .cs3apismanager import CS3APIsManager
from .handlers import handlers


def _jupyter_server_extension_paths():
    return [{
        "module": "cs3api4lab"
    }]

def load_jupyter_server_extension(nb_server_app):
    """ Used as a server extension in order to install the new handlers """
    web_app = nb_server_app.web_app
    for handler in handlers:
        pattern = url_path_join(web_app.settings['base_url'], handler[0])
        new_handler = tuple([pattern] + list(handler[1:]))
        web_app.add_handlers('.*$', [new_handler])