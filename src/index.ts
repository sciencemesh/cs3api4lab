import {ILabShell, ILayoutRestorer, IRouter, JupyterFrontEnd, JupyterFrontEndPlugin,} from '@jupyterlab/application';
// import {DOMUtils} from "@jupyterlab/apputils";
// import { showErrorMessage, Toolbar, ToolbarButton } from '@jupyterlab/apputils';
import {ISettingRegistry} from '@jupyterlab/settingregistry';
import {Dialog, ICommandPalette, showDialog, ToolbarButton, WidgetTracker} from '@jupyterlab/apputils';
import {IDocumentManager} from '@jupyterlab/docmanager';
// import {IMainMenu} from '@jupyterlab/mainmenu';
import {IStateDB} from '@jupyterlab/statedb';
import {pythonIcon} from '@jupyterlab/ui-components';
import {ILauncher} from "@jupyterlab/launcher";
import {each} from "@lumino/algorithm";

// import {LabIcon} from "@jupyterlab/ui-components";

// import {each} from "@lumino/algorithm";
import {ShareWidget} from "./containers/ShareWidget";
import {CreateShareWidget} from "./containers/CreateShareWidget";
import {CS3Contents} from "./CS3Contents";
import {IFileBrowserFactory} from "@jupyterlab/filebrowser/lib/tokens";
import {FileBrowser, FileBrowserModel} from "@jupyterlab/filebrowser";
// import {Contents, ContentsManager} from "@jupyterlab/services";

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CommandIDs {
    export const info = 'filebrowser:cs3-info';
    export const createShare = 'filebrowser:cs3-create-share';
    // export const showBrowser = 'filebrowser:showBrowser';
}

/**
 * The JupyterLab plugin for the CS3api Filebrowser.
 */

const browser: JupyterFrontEndPlugin<void> = {
    id: 'cs3_api_shares',
    requires: [
        IDocumentManager,
        IFileBrowserFactory,
        ILayoutRestorer,
        ISettingRegistry,
        ILabShell,
        IStateDB
    ],
    activate(app: JupyterFrontEnd,
             docManager: IDocumentManager,
             factory: IFileBrowserFactory,
             restorer: ILayoutRestorer,
             labShell: ILabShell,
             settings: ISettingRegistry,
             stateDB: IStateDB
    ): void {
        stateDB.save('share', {share_type: 'by_me'});
        const drive = new CS3Contents(app.docRegistry, stateDB, docManager);

        const browser = factory.createFileBrowser('test', {
            driveName: drive.name,
        });

        docManager.services.contents.addDrive(drive);

        browser.title.caption = 'Shared by me';
        // console.log(browser);
        // browser.toolbar.addItem('cs3_tabbar',);


        browser.toolbar.addItem('cs3_item_shared_filelist', new ToolbarButton({
            onClick: () => {
                stateDB.save('share', {share_type: 'filelist'})
                browser.model.refresh();
                browser.title.caption = 'File list';
            },
            icon: pythonIcon,
            tooltip: `File list`,
            iconClass: 'cs3-item jp-Icon jp-Icon-16'
        }));

        browser.toolbar.addItem('cs3_item_shared_with_me', new ToolbarButton({
            onClick: () => {
                stateDB.save('share', {share_type: 'with_me'})
                browser.model.refresh();
                browser.title.caption = 'Shared with me';
            },
            icon: pythonIcon,
            tooltip: `Shared with me`,
            iconClass: 'cs3-item jp-Icon jp-Icon-16'
        }));

        browser.toolbar.addItem('cs3_item_shared_by_me', new ToolbarButton({
            onClick: () => {
                stateDB.save('share', {share_type: 'by_me'});
                browser.model.refresh();
                browser.title.caption = 'Shared by me';
            },
            icon: pythonIcon,
            tooltip: `Shared by me`,
            iconClass: 'cs3-item jp-Icon jp-Icon-16'
        }));
        // labShell.currentWidget.addClass('testing');

        // const {commands} = app;

        restorer.add(browser, 'cs3_file_browser');
        app.shell.add(browser, 'left', { rank: 101 });

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
                options: IFileBrowserFactory.IOptions = {
                }
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
  id: 'cs3api4lab',
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
              body: new ShareWidget({
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
                return "CS3 info";
            }
        });
    }
};

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
