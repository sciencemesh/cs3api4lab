import {
    ILabShell,
    ILayoutRestorer,
    IRouter,
    JupyterFrontEnd,
    JupyterFrontEndPlugin,
} from '@jupyterlab/application';
import {MainAreaWidget} from '@jupyterlab/apputils';
import {ISettingRegistry} from '@jupyterlab/settingregistry';
import {Dialog, ICommandPalette, showDialog, ToolbarButton, WidgetTracker} from '@jupyterlab/apputils';
import {IDocumentManager} from '@jupyterlab/docmanager';
import {IStateDB} from '@jupyterlab/statedb';
import {checkIcon, circleEmptyIcon, circleIcon, addIcon} from '@jupyterlab/ui-components';
import {ILauncher} from "@jupyterlab/launcher";
import { Launcher } from '@jupyterlab/launcher';
import {IFileBrowserFactory} from "@jupyterlab/filebrowser/lib/tokens";
import {each} from "@lumino/algorithm";

import {CS3Contents} from "./drive";
import {FileBrowser, FileBrowserModel} from "@jupyterlab/filebrowser";
import {ShareWidget} from "./createShare";
import {InfoboxWidget} from "./infobox";

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CommandIDs {
    export const info = 'filebrowser:cs3-info';
    export const createShare = 'filebrowser:cs3-create-share';
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
        stateDB.save('share', {share_type: 'filelist'});
        const drive = new CS3Contents(app.docRegistry, stateDB, docManager);

        const browser = factory.createFileBrowser('test', {
            driveName: drive.name
        });

        const { commands } = app;
        const { model } = browser;


        docManager.services.contents.addDrive(drive);

        browser.title.icon = checkIcon;

        browser.title.caption = 'Shared by me';
        browser.toolbar.addItem('cs3_item_shared_filelist', new ToolbarButton({
            onClick: () => {
                stateDB.save('share', {share_type: 'filelist'})
                browser.model.refresh();
                browser.title.caption = 'File list';
            },
            icon: checkIcon,
            tooltip: `File list`,
            iconClass: 'cs3-item jp-Icon jp-Icon-16'
        }));

        browser.toolbar.addItem('cs3_item_shared_with_me', new ToolbarButton({
            onClick: () => {
                stateDB.save('share', {share_type: 'with_me'})
                browser.model.refresh();
                browser.title.caption = 'Shared with me';
            },
            icon: circleIcon,
            tooltip: `Shared with me`,
            iconClass: 'cs3-item jp-Icon jp-Icon-16'
        }));

        browser.toolbar.addItem('cs3_item_shared_by_me', new ToolbarButton({
            onClick: () => {
                stateDB.save('share', {share_type: 'by_me'});
                browser.model.refresh();
                browser.title.caption = 'Shared by me';
            },
            icon: circleEmptyIcon,
            tooltip: `Shared by me`,
            iconClass: 'cs3-item jp-Icon jp-Icon-16'
        }));

        restorer.add(browser, 'cs3_file_browser');
        app.shell.add(browser, 'left', { rank: 101 });

        if (labShell) {
            const launcher = new ToolbarButton({
                icon: addIcon,
                onClick: () => {
                    return commands
                        .execute('launcher:create', { cwd: model.path })
                        .then((launcher: MainAreaWidget<Launcher>) => {
                            model.pathChanged.connect(() => {
                                if (launcher.content) {
                                    launcher.content.cwd = model.path;
                                }
                            }, launcher);
                            return launcher;
                        });
                },
                tooltip: 'New Launcher'
            });

            browser.toolbar.insertItem(0, 'launch', launcher);
        }
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
        ): any => {
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
                restore: true,
            });

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
                            body: new InfoboxWidget({
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
