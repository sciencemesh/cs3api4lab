import {ILabShell, ILayoutRestorer, IRouter, JupyterFrontEnd, JupyterFrontEndPlugin,} from '@jupyterlab/application';

import {FileBrowser, FileBrowserModel, IFileBrowserFactory} from "@jupyterlab/filebrowser";
import {ISettingRegistry} from '@jupyterlab/settingregistry';
import {Dialog, ICommandPalette, showDialog, Toolbar, ToolbarButton, WidgetTracker} from '@jupyterlab/apputils';
import {IDocumentManager} from '@jupyterlab/docmanager';
import {IMainMenu} from '@jupyterlab/mainmenu';
import {IStateDB} from '@jupyterlab/statedb';
import {pythonIcon} from '@jupyterlab/ui-components';
import {ILauncher} from "@jupyterlab/launcher";
import {each} from "@lumino/algorithm";

// import {LabIcon} from "@jupyterlab/ui-components";

// import {each} from "@lumino/algorithm";
import {Widget} from "./containers/Widget";
import {CreateShareWidget} from "./containers/CreateShareWidget";

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CommandIDs {
    export const info = 'filebrowser:cs3-info';
    export const createShare = 'filebrowser:cs3-create-share';
    // export const showBrowser = 'filebrowser:showBrowser';
}

/**
 * The JupyterLab plugin for the Google Drive Filebrowser.
 */
const browser: JupyterFrontEndPlugin<void> = {
    id: 'cs3_api_filemanager',
    requires: [
        IDocumentManager,
        IFileBrowserFactory,
        ILayoutRestorer,
        IMainMenu,
        ISettingRegistry,
        ILabShell
    ],
    activate(app: JupyterFrontEnd,
             docManager: IDocumentManager,
             factory: IFileBrowserFactory,
             restorer: ILayoutRestorer,
             labShell: ILabShell,
    ): void {
        const browser = Object.assign({}, factory.defaultBrowser);

        console.log(browser);
        // browser.toolbar.addItem('cs3_tabbar',);
        browser.toolbar.addItem('cs3_item',new ToolbarButton({
            onClick: () => {
                console.log('testing cs3 item');
            },
            icon: pythonIcon,
            tooltip: `cs3 item`,
            iconClass: 'cs3-item jp-Icon jp-Icon-16'
        }));
        // labShell.currentWidget.addClass('testing');

        // const {commands} = app;

        // restorer.add(browser, 'cs3_file_browser');
        // browser.title.label = 'test';
        // browser.title.icon =  LabIcon.resolve({
        //     icon: 'ui-components:file'
        // });

        // If the layout is a fresh session without saved data, open file browser.
        // void labShell.restored.then(layout => {
        //     if (layout.fresh) {
        //         console.log('restore filebrwoser');
        //         void commands.execute(CommandIDs.showBrowser, void 0);
        //     }
        // });
    },
    autoStart: true
}


/**
 * The default file browser factory provider.
 */
const factory: JupyterFrontEndPlugin<IFileBrowserFactory> = {
        id: 'cs3_test_factory',
        provides: IFileBrowserFactory,
        requires: [IDocumentManager],
        optional: [IStateDB, IRouter, JupyterFrontEnd.ITreeResolver],
        activate: (
            app: JupyterFrontEnd,
            docManager: IDocumentManager,
            state: IStateDB | null,
            router: IRouter | null,
            tree: JupyterFrontEnd.ITreeResolver | null
        ): any => {
            // const { commands } = app;
            const tracker = new WidgetTracker<FileBrowser>({namespace: 'cs3_test'});
            const createFileBrowser = (
                id: string,
                options: IFileBrowserFactory.IOptions = {}
            ) => {
                const model = new FileBrowserModel({
                    auto: options.auto ?? true,
                    manager: docManager,
                    driveName: options.driveName || '',
                    refreshInterval: options.refreshInterval,
                    state:
                        options.state === null ? undefined : options.state || state || undefined
                });
                const restore = options.restore;
                const widget = new FileBrowser({id, model, restore});

                const cs3toolbar = new Toolbar();
                // cs3toolbar.addClass('cs3_tab_toolbar');
                cs3toolbar.insertBefore('launch', 'cs3_new_toolbar', new ToolbarButton({
                        label: 'Files',
                        icon: pythonIcon,
                        onClick: () => {
                            console.log('testing new button');
                        }
                    }
                ));
                console.log(widget.toolbar.insertItem(0, 'cs3_test', cs3toolbar));


                // Add a launcher toolbar item.
                // const launcher = new ToolbarButton({
                //     icon: addIcon,
                //     onClick: () => {
                //         if (commands.hasCommand('launcher:create')) {
                //             return Private.createLauncher(commands, widget);
                //         }
                //     },
                //     tooltip: 'New Launcher'
                // });
                // widget.toolbar.insertItem(0, 'launch', launcher);

                // Track the newly created file browser.
                void tracker.add(widget);

                return widget;
            };

// Manually restore and load the default file browser.
            const defaultBrowser = createFileBrowser('filebrowser', {
                auto: true,
                restore: false
            });
// void Private.restoreBrowser(defaultBrowser, commands, router, tree);

            return {createFileBrowser, defaultBrowser, tracker};
        }
    }
;

/**
 * Initialization data for the cs3api4lab extension.
 */
const cs3info: JupyterFrontEndPlugin<void> = {
  id: 'cs3api_test_ext',
  autoStart: true,
  requires: [IFileBrowserFactory, ISettingRegistry, ICommandPalette],
  optional: [ILauncher],
  activate: async (app: JupyterFrontEnd, factory: IFileBrowserFactory) => {
    const { commands } = app;
    const { tracker } = factory;

    app.contextMenu.addItem({
      command: CommandIDs.info,
      selector: '.jp-DirListing-item', // show only for file/directory items.
      rank: 3
    });

    // Add the CS3 share to file browser context menu
    commands.addCommand(CommandIDs.info, {
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
        return "CS3 info";
      }
    });
  }
};

/**
 * Initialization data for the cs3api4lab extension.
 */
const cs3share: JupyterFrontEndPlugin<void> = {
    id: 'cs3_share',
    autoStart: true,
    requires: [IFileBrowserFactory, ISettingRegistry, ICommandPalette],
    optional: [ILauncher],
    activate: async (app: JupyterFrontEnd, factory: IFileBrowserFactory) => {
        const { commands } = app;
        const { tracker } = factory;

        app.contextMenu.addItem({
            command: CommandIDs.createShare,
            selector: '.jp-DirListing-item', // show only for file/directory items.
            rank: 3
        });

        // Add the CS3 share to file browser context menu
        commands.addCommand(CommandIDs.createShare, {
            execute: () => {
                const widget = tracker.currentWidget;
                if (widget) {
                    each(widget.selectedItems(), fileInfo => {
                        showDialog({
                            body: new CreateShareWidget({
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

// export default extension;

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [
    factory,
    browser,
    cs3info,
    cs3share
];
export default plugins;
