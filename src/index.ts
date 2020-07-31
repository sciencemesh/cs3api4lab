import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { MainAreaWidget } from '@jupyterlab/apputils';
import { ILauncher } from '@jupyterlab/launcher';
import { reactIcon } from '@jupyterlab/ui-components';

//components
import {Widget} from "./containers/Widget";

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CommandIDs {
  export const create = 'create-react-widget';
}

/**
 * Initialization data for the cs3api4lab extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'cs3api_test_ext',
  autoStart: true,
  optional: [ILauncher],
  activate: async (app: JupyterFrontEnd, launcher: ILauncher)=> {
    const { commands } = app;
    const command = CommandIDs.create;

    commands.addCommand(command, {
      caption: 'CS3 API Test',
      label: 'CS3 API',
      icon: args => (args['isPalette'] ? null : reactIcon),
      execute: () => {
        const content = new Widget();
        const widget = new MainAreaWidget<Widget>({ content });
        widget.title.label = 'CS3 API';
        app.shell.add(widget, 'main');
      }
    });

    if (launcher) {
      launcher.add({
        command
      });
    }
  }
};

export default extension;
