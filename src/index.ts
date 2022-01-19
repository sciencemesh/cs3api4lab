import {
  ILabShell,
  IRouter,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import {
  Dialog,
  ICommandPalette,
  ReactWidget,
  WidgetTracker
} from '@jupyterlab/apputils';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { IStateDB } from '@jupyterlab/statedb';
import { ILauncher } from '@jupyterlab/launcher';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser/lib/tokens';
import { each } from '@lumino/algorithm';

import {
  CS3Contents,
  CS3ContentsShareByMe,
  CS3ContentsShareWithMe
} from './drive';
import { FileBrowser, FilterFileBrowserModel } from '@jupyterlab/filebrowser';
import { InfoboxWidget } from './infobox';
import {
  Cs3BottomWidget,
  Cs3HeaderWidget,
  Cs3Panel,
  Cs3TabWidget
} from './cs3panel';
import { addLaunchersButton, createShareBox } from './utils';
import { SplitPanel, Widget } from '@lumino/widgets';
import {
  kernelIcon,
  caseSensitiveIcon,
  inspectorIcon,
  newFolderIcon
} from '@jupyterlab/ui-components';
import { Contents } from '@jupyterlab/services';

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CommandIDs {
  export const info = 'filebrowser:cs3-info';
  export const createShare = 'filebrowser:cs3-create-share';
}

/**
 * The default file browser factory provider.
 */
const factory: JupyterFrontEndPlugin<IFileBrowserFactory> = {
  id: 'cs3_test_factory',
  provides: IFileBrowserFactory,
  requires: [IDocumentManager],
  optional: [IStateDB, IRouter, JupyterFrontEnd.ITreeResolver],
  autoStart: true,
  activate: (
    app: JupyterFrontEnd,
    docManager: IDocumentManager,
    state: IStateDB | null
  ): any => {
    const tracker = new WidgetTracker<FileBrowser>({ namespace: 'cs3_test' });

    const createFileBrowser = (
      id: string,
      options: IFileBrowserFactory.IOptions = {}
    ): FileBrowser => {
      const model = new FilterFileBrowserModel({
        auto: options.auto ?? true,
        manager: docManager,
        driveName: options.driveName || '',
        refreshInterval: options.refreshInterval,
        state:
          options.state === null
            ? undefined
            : options.state || state || undefined
      });
      // Get the file path changed signal.
      model.fileChanged.connect(() => {
        void model.refresh();
      });

      const restore = options.restore;
      const widget = new FileBrowser({ id, model, restore });

      // Track the newly created file browser.
      void tracker.add(widget);

      return widget;
    };

    // Manually restore and load the default file browser.
    const defaultBrowser = createFileBrowser('filebrowser', {
      auto: true,
      restore: true
    });

    return { createFileBrowser, defaultBrowser, tracker };
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
        const dialogTracker = new WidgetTracker<Dialog<any>>({
          namespace: '@jupyterlab/apputils:Dialog'
        });

        if (widget) {
          each(widget.selectedItems(), fileInfo => {
            const dialog = new Dialog({
              body: new InfoboxWidget({
                fileInfo: fileInfo,
                widgetTracker: dialogTracker
              }),
              buttons: [Dialog.okButton({ label: 'Close' })]
            });

            dialog.activate();
            dialog.show();
            dialog.launch();
            dialogTracker.add(dialog);
          });
        }
      },
      iconClass: () => 'jp-MaterialIcon jp-FileUploadIcon',
      label: () => {
        return 'CS3 info';
      }
    });
  }
};

/**
 * The JupyterLab plugin for the CS3api Filebrowser.
 * New filemanager layout version
 */
const cs3browser: JupyterFrontEndPlugin<void> = {
  id: 'cs3_api_shares_v2',
  requires: [IDocumentManager, IFileBrowserFactory, ILabShell, IStateDB],
  autoStart: true,
  activate(
    app: JupyterFrontEnd,
    docManager: IDocumentManager,
    factory: IFileBrowserFactory,
    labShell: ILabShell,
    stateDB: IStateDB
  ): void {
    const cs3Panel = new Cs3Panel(
      'cs3 panel',
      'cs3-panel',
      kernelIcon,
      {},
      stateDB
    );

    void stateDB.save('share', { shareType: 'filelist' });
    void stateDB.save('showHidden', false);

    //
    // Header
    //
    const cs3HeaderWidget: ReactWidget = new Cs3HeaderWidget(
      'cs3Api4Lab',
      'cs3-header-widget'
    );
    cs3Panel.addHeader(cs3HeaderWidget);

    //
    // CS3 File browser
    //
    const drive: Contents.IDrive = new CS3Contents(
      app.docRegistry,
      stateDB,
      docManager,
      app.serviceManager.serverSettings
    );
    const fileBrowser = factory.createFileBrowser('fileBrowser', {
      driveName: drive.name
    });
    fileBrowser.title.label = 'My Files';
    fileBrowser.title.caption = 'My Files';
    fileBrowser.title.icon = caseSensitiveIcon;
    docManager.services.contents.addDrive(drive);

    //
    // Bottom
    //
    const cs3BottomWidget: ReactWidget = new Cs3BottomWidget(
      'cs3Api Bottom',
      'cs3-bottom-widget',
      {},
      stateDB,
      fileBrowser,
      drive
    );
    cs3Panel.addBottom(cs3BottomWidget);

    addLaunchersButton(app, fileBrowser, labShell);

    //
    // Share split panel
    //
    const splitPanel = new SplitPanel();
    splitPanel.id = 'sharesPanel';
    splitPanel.spacing = 5;
    splitPanel.orientation = 'vertical';
    splitPanel.title.iconClass = 'jp-example-view';
    splitPanel.title.caption = 'Shares';
    splitPanel.title.label = 'Shares';
    splitPanel.title.icon = inspectorIcon;

    //
    // ShareByMe
    //
    const driveShareByMe: Contents.IDrive = new CS3ContentsShareByMe(
      app.docRegistry,
      stateDB,
      docManager,
      app.serviceManager.serverSettings
    );
    const fileBrowserSharedByMe: FileBrowser = factory.createFileBrowser(
      'fileBrowserSharedByMe',
      {
        driveName: driveShareByMe.name
      }
    );
    fileBrowserSharedByMe.toolbar.hide();

    const shareByMePanel: Widget = createShareBox(
      'cs3-share-by-me',
      'Shared by Me',
      fileBrowserSharedByMe
    );
    splitPanel.addWidget(shareByMePanel);

    docManager.services.contents.addDrive(driveShareByMe);

    //
    // ShareWithMe
    //
    const driveShareWithMe: Contents.IDrive = new CS3ContentsShareWithMe(
      app.docRegistry,
      stateDB,
      docManager,
      app.serviceManager.serverSettings
    );
    const fileBrowserSharedWithMe: FileBrowser = factory.createFileBrowser(
      'fileBrowserSharedWithMe',
      {
        driveName: driveShareWithMe.name
      }
    );
    fileBrowserSharedWithMe.toolbar.hide();

    const shareWithMePanel = createShareBox(
      'cs3-share-with-me',
      'Share with Me',
      fileBrowserSharedWithMe
    );
    splitPanel.addWidget(shareWithMePanel);

    docManager.services.contents.addDrive(driveShareWithMe);

    //
    // Example tab
    //
    const cs3TabWidget3: ReactWidget = new Cs3TabWidget(
      'Projects',
      newFolderIcon
    );

    cs3Panel.addTab(fileBrowser);
    cs3Panel.addTab(cs3TabWidget3);
    cs3Panel.addTab(splitPanel);

    cs3Panel.sharesTabVisible().connect(() => {
      fileBrowserSharedWithMe.model.refresh();
      fileBrowserSharedByMe.model.refresh();
    });

    window.addEventListener('resize', () => {
      cs3Panel.fit();
    });

    app.shell.add(cs3Panel, 'left', { rank: 103 });
    cs3Panel.activate();
  }
};

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [cs3browser, factory, cs3share];
export default plugins;
