import {JupyterFrontEnd, JupyterFrontEndPlugin} from '@jupyterlab/application';
import {ILauncher} from '@jupyterlab/launcher';
import {IFileBrowserFactory} from "@jupyterlab/filebrowser";
import {ISettingRegistry} from '@jupyterlab/settingregistry';
import { showDialog, Dialog, ICommandPalette } from '@jupyterlab/apputils';

import {each} from "@lumino/algorithm";
import {Widget} from "./containers/Widget";

// import { showErrorMessage } from "@jupyterlab/apputils";

// import {IFileBrowserFactory} from '@jupyterlab/filebrowser';

// import {toArray} from '@lumino/algorithm';

// import {reactIcon} from '@jupyterlab/ui-components';
//components
// import {Widget} from "./containers/Widget";

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CommandIDs {
  export const share = 'filebrowser:cs3-share';
  export const duplicate = 'filebrowser:duplicate';
}

/**
 * Initialization data for the cs3api4lab extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'cs3api_test_ext',
  autoStart: true,
  requires: [IFileBrowserFactory, ISettingRegistry, ICommandPalette],
  optional: [ILauncher],
  activate: async (app: JupyterFrontEnd, factory: IFileBrowserFactory) => {
    const {commands} = app;
    const {tracker} = factory;

    app.contextMenu.addItem({
      command: CommandIDs.share,
      selector: '.jp-DirListing-item', // show only for file/directory items.
      rank: 3
    });

    // Add the CS3 share to file browser context menu
    commands.addCommand(CommandIDs.share, {
      execute: () => {
        const widget = tracker.currentWidget;
        if (widget) {
          each(widget.selectedItems(), fileInfo => {
            showDialog({
              body: new Widget({
                fileInfo: fileInfo
              }),
              buttons: [Dialog.okButton({label: 'Close'})]
            });
          });
        }
      },
      iconClass: () => "jp-MaterialIcon jp-FileUploadIcon",
      label: () => {
        return "CS3 share";
      }
    });
  }
};

export default extension;
