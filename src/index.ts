import {
  ILabShell,
  ILayoutRestorer,
  IRouter,
  ITreePathUpdater,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import {
  Dialog,
  ICommandPalette,
  ReactWidget,
  ToolbarButton,
  WidgetTracker
} from '@jupyterlab/apputils';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { IStateDB } from '@jupyterlab/statedb';
import { ILauncher } from '@jupyterlab/launcher';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser/lib/tokens';
import { each, toArray } from '@lumino/algorithm';

import {
  CS3Contents,
  CS3ContentsShareByMe,
  CS3ContentsShareWithMe
} from './drive';
import { FileBrowser, FilterFileBrowserModel } from '@jupyterlab/filebrowser';
import { createInfobox } from './infobox';
import {
  Cs3BottomWidget,
  // Cs3BottomWidget,
  Cs3HeaderWidget,
  Cs3Panel,
  Cs3TabWidget
} from './cs3panel';
import { PendingSharesListWrapper } from './pendingShares';
import { addHomeDirButton, addLaunchersButton } from './utils';
import { AccordionPanel } from '@lumino/widgets';
import { kernelIcon } from '@jupyterlab/ui-components';
import { Contents } from '@jupyterlab/services';
import { addCommands, createLauncher, restoreBrowser } from './browserCommands';
import { IMainMenu } from '@jupyterlab/mainmenu';
import { ITranslator } from '@jupyterlab/translation';
import { requestAPI } from './services';
import { infoIcon, shareIcon } from './icons';

/**
 * The command IDs used by the react-widget plugin.
 */
namespace CS3CommandIDs {
  export const info = 'cs3filebrowser:cs3-info';
  export const shareInfo = 'cs3filebrowser:cs3-share-info';
  export const createShare = 'cs3filebrowser:cs3-create-share';
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
    state: IStateDB,
    router: IRouter | null,
    tree: JupyterFrontEnd.ITreeResolver | null
  ): any => {
    const tracker = new WidgetTracker<FileBrowser>({ namespace: 'cs3_test' });
    const { commands } = app;

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

    //
    // CS3 File browser
    //
    docManager.services.contents.dispose();
    const drive: Contents.IDrive = new CS3Contents(
      app.docRegistry,
      state,
      docManager,
      app.serviceManager.serverSettings
    );
    docManager.services.contents.addDrive(drive);

    // Manually restore and load the default file browser.
    const defaultBrowser = createFileBrowser('cs3filebrowser', {
      auto: true,
      restore: false,
      driveName: 'cs3Files'
    });

    void restoreBrowser(defaultBrowser, commands, router, tree);

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
      command: CS3CommandIDs.info,
      selector: '.jp-DirListing-item', // show only for file/directory items.
      rank: 3
    });

    app.contextMenu.addItem({
      command: CS3CommandIDs.shareInfo,
      selector: '.jp-DirListing-item', // show only for file/directory items.
      rank: 3
    });

    app.contextMenu.addItem({
      command: CS3CommandIDs.createShare,
      selector: '.jp-DirListing-item', // show only for file/directory items.
      rank: 3
    });

    // Add the CS3 share to file browser context menu
    commands.addCommand(CS3CommandIDs.info, {
      execute: () => {
        const widget = tracker.currentWidget;
        const dialogTracker = new WidgetTracker<Dialog<any>>({
          namespace: '@jupyterlab/apputils:Dialog'
        });
        const drive = widget?.model.driveName.toString();
        const item = widget?.selectedItems().next();
        if (item) {
          const fileInfo = Object.assign({}, item, {
            path: item.path.replace(drive + ':', '/')
          });
          const dialog = createInfobox(fileInfo, 'info');
          dialog.launch();
          dialogTracker.add(dialog);
        }
      },
      // iconClass: () => 'jp-MaterialIcon jp-FileUploadIcon',
      icon: infoIcon,
      label: () => {
        return 'File info';
      }
    });

    // Add the CS3 share to file browser context menu
    commands.addCommand(CS3CommandIDs.createShare, {
      execute: () => {
        const widget = tracker.currentWidget;
        const dialogTracker = new WidgetTracker<Dialog<any>>({
          namespace: '@jupyterlab/apputils:Dialog'
        });

        if (widget) {
          const drive = widget.model.driveName.toString();
          each(widget.selectedItems(), item => {
            const fileInfo = Object.assign({}, item, {
              path: item.path.replace(drive + ':', '/')
            });
            const dialog = createInfobox(fileInfo, 'shares');
            dialog.launch();
            dialogTracker.add(dialog);
          });
        }
      },
      // iconClass: () => 'jp-MaterialIcon jp-FileUploadIcon',
      icon: shareIcon,
      label: () => {
        return 'Share file';
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
  requires: [
    IDocumentManager,
    IFileBrowserFactory,
    ILabShell,
    IStateDB,
    ILayoutRestorer,
    ISettingRegistry,
    ITranslator
  ],
  optional: [ITreePathUpdater, ICommandPalette, IMainMenu],
  autoStart: true,
  activate(
    app: JupyterFrontEnd,
    docManager: IDocumentManager,
    factory: IFileBrowserFactory,
    labShell: ILabShell,
    stateDB: IStateDB,
    restorer: ILayoutRestorer,
    settingRegistry: ISettingRegistry,
    translator: ITranslator,
    treePathUpdater: ITreePathUpdater | null,
    commandPalette: ICommandPalette | null,
    mainMenu: IMainMenu | null
  ): void {
    // const browser = factory.defaultBrowser;
    const { commands } = app;
    const cs3Panel = new Cs3Panel(
      'cs3 panel',
      'cs3-panel',
      kernelIcon,
      {},
      stateDB
    );

    void stateDB.save('activeTab', 'cs3filebrowser');
    void stateDB.save('share', { shareType: 'filelist' });
    void stateDB.save('showHidden', false);
    requestAPI('/api/cs3/user/home_dir', {
      method: 'get'
    }).then(homeDir => {
      if (homeDir) {
        void stateDB.save('homeDir', homeDir as string);
      }
    });

    //
    // Header
    //
    const cs3HeaderWidget: ReactWidget = new Cs3HeaderWidget(
      'cs3Api4Lab',
      'cs3-header-widget'
    );
    cs3Panel.addHeader(cs3HeaderWidget);

    // const fileBrowser = factory.defaultBrowser
    factory.defaultBrowser.title.label = 'My Files';
    factory.defaultBrowser.title.caption = 'My Files';
    factory.defaultBrowser.title.className = 'jp-main-tab';
    factory.defaultBrowser.title.iconClass = 'jp-main-tab-icon';
    // factory.defaultBrowser.title.icon = caseSensitiveIcon;

    factory.defaultBrowser.toolbar.addItem(
      'Share files',
      new ToolbarButton({
        icon: shareIcon,
        tooltip: 'Share files',
        onClick: () => {
          const selectedFileList: Contents.IModel[] = toArray(
            factory.defaultBrowser.selectedItems()
          );

          if (selectedFileList.length <= 0) {
            alert('select a file');
            return;
          }

          const dialogTracker = new WidgetTracker<Dialog<any>>({
            namespace: '@jupyterlab/apputils:Dialog'
          });

          each(factory.defaultBrowser.selectedItems(), file => {
            const dialog = createInfobox(file, 'shares');
            void dialog.launch();
            void dialogTracker.add(dialog);
          });
        }
      })
    );

    //
    // Bottom
    //
    const cs3BottomWidget: ReactWidget = new Cs3BottomWidget(
      'cs3Api Bottom',
      'cs3-bottom-widget',
      {
        // he
      },
      stateDB,
      factory.defaultBrowser
    );
    cs3Panel.addBottom(cs3BottomWidget);

    addLaunchersButton(app, factory.defaultBrowser, labShell);
    addHomeDirButton(app, factory.defaultBrowser, labShell, stateDB);

    //
    // ShareByMe
    //
    const driveShareByMe: Contents.IDrive = new CS3ContentsShareByMe(
      app.docRegistry,
      stateDB,
      docManager,
      app.serviceManager.serverSettings
    );

    docManager.services.contents.addDrive(driveShareByMe);
    const fileBrowserSharedByMe: FileBrowser = factory.createFileBrowser(
      'fileBrowserSharedByMe',
      {
        driveName: driveShareByMe.name
      }
    );
    fileBrowserSharedByMe.toolbar.hide();

    //
    // ShareWithMe
    //
    const driveShareWithMe: Contents.IDrive = new CS3ContentsShareWithMe(
      app.docRegistry,
      stateDB,
      docManager,
      app.serviceManager.serverSettings
    );
    docManager.services.contents.addDrive(driveShareWithMe);

    const fileBrowserSharedWithMe: FileBrowser = factory.createFileBrowser(
      'fileBrowserSharedWithMe',
      {
        driveName: driveShareWithMe.name
      }
    );
    fileBrowserSharedWithMe.toolbar.hide();

    //
    // Projects tab
    //
    const cs3TabWidget3: ReactWidget = new Cs3TabWidget(
      'Projects'
      // newFolderIcon
    );

    /**
     * Add commands - this is a part of filebrowser-plugin
     * Copied from packages/filebrowser-extension/src/index.ts:325
     */
    addCommands(
      app,
      factory,
      labShell,
      docManager,
      settingRegistry,
      translator,
      commandPalette,
      mainMenu
    );

    /**
     * Copied from packages/filebrowser-extension/src/index.ts:364
     * cs3api4lab modification - try to redirect to user directory after restoration
     */
    void Promise.all([
      app.restored,
      factory.defaultBrowser.model.restored
    ]).then(() => {
      function maybeCreate() {
        // Create a launcher if there are no open items.
        if (
          labShell.isEmpty('main') &&
          commands.hasCommand('launcher:create')
        ) {
          void createLauncher(commands, factory.defaultBrowser);
        }
      }

      // redirect to user directory
      stateDB.fetch('homeDir').then(homeDir => {
        if (homeDir) {
          void factory.defaultBrowser.model.cd(homeDir as string);
        }
      });

      // When layout is modified, create a launcher if there are no open items.
      labShell.layoutModified.connect(() => {
        maybeCreate();
      });
    });

    /**
     * Copied from packages/filebrowser-extension/src/index.ts:377
     */
    let navigateToCurrentDirectory = false;
    let useFuzzyFilter = true;

    /**
     * Copied from packages/filebrowser-extension/src/index.ts:380
     * Changes: use new file browser instance from cs3api4lab plugin
     */
    void settingRegistry
      .load('@jupyterlab/filebrowser-extension:browser')
      .then(settings => {
        settings.changed.connect(settings => {
          navigateToCurrentDirectory = settings.get(
            'navigateToCurrentDirectory'
          ).composite as boolean;
          factory.defaultBrowser.navigateToCurrentDirectory = navigateToCurrentDirectory;
        });
        navigateToCurrentDirectory = settings.get('navigateToCurrentDirectory')
          .composite as boolean;
        factory.defaultBrowser.navigateToCurrentDirectory = navigateToCurrentDirectory;
        settings.changed.connect(settings => {
          useFuzzyFilter = settings.get('useFuzzyFilter').composite as boolean;
          factory.defaultBrowser.useFuzzyFilter = useFuzzyFilter;
        });
        useFuzzyFilter = settings.get('useFuzzyFilter').composite as boolean;
        factory.defaultBrowser.useFuzzyFilter = useFuzzyFilter;
      });

    // Create shares panel
    const cs3Accordion = new AccordionPanel();
    cs3Accordion.id = 'sharesPanel';
    cs3Accordion.title.caption = 'Shares';
    cs3Accordion.title.label = 'Shares';
    cs3Accordion.title.iconClass = 'jp-main-tab-icon';
    cs3Accordion.title.className = 'jp-main-tab';
    cs3Accordion.hide();

    const pendingShares = new PendingSharesListWrapper();
    pendingShares.title.label = 'Pending shares';
    fileBrowserSharedByMe.title.label = 'Shared by me';
    fileBrowserSharedWithMe.title.label = 'Shared with me';

    // fold accordion widget
    pendingShares.hide();

    cs3Accordion.insertWidget(1, pendingShares);
    cs3Accordion.insertWidget(2, fileBrowserSharedByMe);
    cs3Accordion.insertWidget(3, fileBrowserSharedWithMe);
    cs3Accordion.setRelativeSizes([100, 400, 400]);

    cs3Panel.addTab(factory.defaultBrowser);
    cs3Panel.addTab(cs3TabWidget3);
    cs3Panel.addTab(cs3Accordion);

    // refresh shares on share tab activation
    cs3Panel.sharesTabVisible().connect(() => {
      void fileBrowserSharedWithMe.model.refresh();
      void fileBrowserSharedByMe.model.refresh();
    });

    // refresh files on share tab activation
    cs3Panel.filesTabVisible().connect(() => {
      void factory.defaultBrowser.model.refresh();
    });

    window.addEventListener('resize', () => {
      cs3Panel.fit();
    });

    app.shell.add(cs3Panel, 'left', { rank: 103 });
    restorer.add(cs3Panel, 'cs3_filebrowser');

    void labShell.restored.then(() => {
      app.shell.activateById(cs3Panel.id); // activate cs3 file browser at the start of session
      if (labShell.mode !== 'single-document') {
        // add launcher to file browser
        if (
          labShell.isEmpty('main') &&
          commands.hasCommand('launcher:create')
        ) {
          void createLauncher(commands, factory.defaultBrowser);
        }
      }
    });
  }
};

/**
 * Export the plugins as default.
 */
const plugins: JupyterFrontEndPlugin<any>[] = [cs3browser, factory, cs3share];
export default plugins;
