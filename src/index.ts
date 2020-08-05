import {ILabShell, ILayoutRestorer, JupyterFrontEnd, JupyterFrontEndPlugin,} from '@jupyterlab/application';

import {IFileBrowserFactory} from "@jupyterlab/filebrowser";
import {ISettingRegistry} from '@jupyterlab/settingregistry';
import {ICommandPalette} from '@jupyterlab/apputils';
import {IDocumentManager} from '@jupyterlab/docmanager';
import {IMainMenu} from '@jupyterlab/mainmenu';
// import {LabIcon} from "@jupyterlab/ui-components";

// import {each} from "@lumino/algorithm";
// import {Widget} from "./containers/Widget";

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CommandIDs {
    export const share = 'filebrowser:cs3-share';
    export const showBrowser = 'filebrowser:showBrowser';
}

/**
 * The JupyterLab plugin for the Google Drive Filebrowser.
 */
const extension: JupyterFrontEndPlugin<void> = {
    id: 'cs3_api_filemanager',
    requires: [
        ICommandPalette,
        IDocumentManager,
        IFileBrowserFactory,
        ILayoutRestorer,
        IMainMenu,
        ISettingRegistry
    ],
    activate(app: JupyterFrontEnd,
             docManager: IDocumentManager,
             factory: IFileBrowserFactory,
             restorer: ILayoutRestorer,
             labShell: ILabShell,
    ): void {
        console.log(app, docManager, factory, restorer, labShell);
        const browser = Object.assign({}, factory.defaultBrowser);
        browser.addClass('cs3_test_filebrowser');

        console.log(browser);
        const {commands} = app;

        // restorer.add(browser, 'cs3_file_browser');
        browser.title.label = 'test';
        // browser.title.icon =  LabIcon.resolve({
        //     icon: 'ui-components:file'
        // });

        // labShell.add(browser, 'left', {rank: 100});

        // If the layout is a fresh session without saved data, open file browser.
        void labShell.restored.then(layout => {
            if (layout.fresh) {
                console.log('restore filebrwoser');
                void commands.execute(CommandIDs.showBrowser, void 0);
            }
        });

        console.log('render filebrowser');
    },
    autoStart: true
}
export default extension;

/**
 * Initialization data for the cs3api4lab extension.
 */
// const extension: JupyterFrontEndPlugin<void> = {
//   id: 'cs3api_test_ext',
//   autoStart: true,
//   requires: [IFileBrowserFactory, ISettingRegistry, ICommandPalette],
//   optional: [ILauncher],
//   activate: async (app: JupyterFrontEnd, factory: IFileBrowserFactory) => {
//     const { commands } = app;
//     const { tracker } = factory;
//
//     app.contextMenu.addItem({
//       command: CommandIDs.share,
//       selector: '.jp-DirListing-item', // show only for file/directory items.
//       rank: 3
//     });
//
//     // Add the CS3 share to file browser context menu
//     commands.addCommand(CommandIDs.share, {
//       execute: () => {
//         const widget = tracker.currentWidget;
//         if (widget) {
//           each(widget.selectedItems(), fileInfo => {
//             showDialog({
//               body: new Widget({
//                 fileInfo: fileInfo
//               }),
//               buttons: [Dialog.okButton({label: 'Close'})]
//             });
//           });
//         }
//       },
//       iconClass: () => "jp-MaterialIcon jp-FileUploadIcon",
//       label: () => {
//         return "CS3 share";
//       }
//     });
//   }
// };

// export default extension;
