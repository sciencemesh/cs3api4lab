import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';


/**
 * Initialization data for the cs3api4lab extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'cs3api4lab',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension cs3api4lab is activated!');
  }
};

export default extension;
