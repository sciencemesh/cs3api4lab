/**
 * This is a copy of upstream code of filebrowser-plugin (version 3.0.x) with some modifications to fit our plugin.
 * Copied from https://github.com/jupyterlab/jupyterlab.git - branch 3.0.x
 * Path to file: packages/filebrowser-extension/src/index.ts
 */

/**
 * The command IDs used by the file browser plugin.
 */
import { ILabShell, IRouter, JupyterFrontEnd } from '@jupyterlab/application';
import { IFileBrowserFactory } from '@jupyterlab/filebrowser/lib/tokens';
import { IDocumentManager } from '@jupyterlab/docmanager';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { ITranslator } from '@jupyterlab/translation';
import {
  Clipboard,
  DOMUtils,
  ICommandPalette,
  InputDialog,
  MainAreaWidget,
  showErrorMessage
} from '@jupyterlab/apputils';
import { IMainMenu } from '@jupyterlab/mainmenu';
import {
  addIcon,
  closeIcon,
  copyIcon,
  cutIcon,
  downloadIcon,
  editIcon,
  fileIcon,
  folderIcon,
  markdownIcon,
  newFolderIcon,
  pasteIcon,
  stopIcon,
  textEditorIcon
} from '@jupyterlab/ui-components';
import { FileBrowser } from '@jupyterlab/filebrowser';
import { Launcher } from '@jupyterlab/launcher';
import { CommandRegistry } from '@lumino/commands';
import { Message } from '@lumino/messaging';
import { Menu } from '@lumino/widgets';
import { PathExt } from '@jupyterlab/coreutils';
import { Contents } from '@jupyterlab/services';
import { IIterator, map, reduce, toArray } from '@lumino/algorithm';

/**
 * Copied from packages/filebrowser-extension/src/index.ts:81
 */
namespace CommandIDs {
  export const copy = 'filebrowser:copy';

  export const copyDownloadLink = 'filebrowser:copy-download-link';

  // For main browser only.
  export const createLauncher = 'filebrowser:create-main-launcher';

  export const cut = 'filebrowser:cut';

  export const del = 'filebrowser:delete';

  export const download = 'filebrowser:download';

  export const duplicate = 'filebrowser:duplicate';

  // For main browser only.
  export const hideBrowser = 'filebrowser:hide-main';

  export const goToPath = 'filebrowser:go-to-path';

  export const openPath = 'filebrowser:open-path';

  export const open = 'filebrowser:open';

  export const openBrowserTab = 'filebrowser:open-browser-tab';

  export const paste = 'filebrowser:paste';

  export const createNewDirectory = 'filebrowser:create-new-directory';

  export const createNewFile = 'filebrowser:create-new-file';

  export const createNewMarkdownFile = 'filebrowser:create-new-markdown-file';

  export const rename = 'filebrowser:rename';

  // For main browser only.
  export const share = 'filebrowser:share-main';

  // For main browser only.
  export const copyPath = 'filebrowser:copy-path';

  export const showBrowser = 'filebrowser:activate';

  export const shutdown = 'filebrowser:shutdown';

  // For main browser only.
  export const toggleBrowser = 'filebrowser:toggle-main';

  export const toggleNavigateToCurrentDirectory =
    'filebrowser:toggle-navigate-to-current-directory';

  export const toggleLastModified = 'filebrowser:toggle-last-modified';

  export const search = 'filebrowser:search';
}

/**
 * Add the main file browser commands to the application's command registry.
 * Copied from packages/filebrowser-extension/src/index.ts:468 // added export
 */
export function addCommands(
  app: JupyterFrontEnd,
  factory: IFileBrowserFactory,
  labShell: ILabShell,
  docManager: IDocumentManager,
  settingRegistry: ISettingRegistry,
  translator: ITranslator,
  commandPalette: ICommandPalette | null,
  mainMenu: IMainMenu | null
): void {
  const trans = translator.load('jupyterlab');
  const { docRegistry: registry, commands } = app;
  const { defaultBrowser: browser, tracker } = factory;

  commands.addCommand(CommandIDs.del, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.delete();
      }
    },
    icon: closeIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Delete'),
    mnemonic: 0
  });

  commands.addCommand(CommandIDs.copy, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.copy();
      }
    },
    icon: copyIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Copy'),
    mnemonic: 0
  });

  commands.addCommand(CommandIDs.cut, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.cut();
      }
    },
    icon: cutIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Cut')
  });

  commands.addCommand(CommandIDs.download, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.download();
      }
    },
    icon: downloadIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Download')
  });

  commands.addCommand(CommandIDs.duplicate, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.duplicate();
      }
    },
    icon: copyIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Duplicate')
  });

  commands.addCommand(CommandIDs.hideBrowser, {
    execute: () => {
      const widget = tracker.currentWidget;
      if (widget && !widget.isHidden) {
        labShell.collapseLeft();
      }
    }
  });

  commands.addCommand(CommandIDs.goToPath, {
    execute: async args => {
      const path = (args.path as string) || '';
      const showBrowser = !(args?.dontShowBrowser ?? false);
      try {
        const item = await Private.navigateToPath(path, factory, translator);
        if (item.type !== 'directory' && showBrowser) {
          const browserForPath = Private.getBrowserForPath(path, factory);
          if (browserForPath) {
            browserForPath.clearSelectedItems();
            const parts = path.split('/');
            const name = parts[parts.length - 1];
            if (name) {
              await browserForPath.selectItemByName(name);
            }
          }
        }
      } catch (reason) {
        console.warn(`${CommandIDs.goToPath} failed to go to: ${path}`, reason);
      }
      if (showBrowser) {
        return commands.execute(CommandIDs.showBrowser, { path });
      }
    }
  });

  commands.addCommand(CommandIDs.openPath, {
    label: args =>
      args.path ? trans.__('Open %1', args.path) : trans.__('Open from Path…'),
    caption: args =>
      args.path ? trans.__('Open %1', args.path) : trans.__('Open from path'),
    execute: async args => {
      let path: string | undefined;
      if (args?.path) {
        path = args.path as string;
      } else {
        path =
          (
            await InputDialog.getText({
              label: trans.__('Path'),
              placeholder: '/path/relative/to/jlab/root',
              title: trans.__('Open Path'),
              okLabel: trans.__('Open')
            })
          ).value ?? undefined;
      }
      if (!path) {
        return;
      }
      try {
        const trailingSlash = path !== '/' && path.endsWith('/');
        if (trailingSlash) {
          // The normal contents service errors on paths ending in slash
          path = path.slice(0, path.length - 1);
        }
        path = path ?? '/';
        const browserForPath: FileBrowser = Private.getBrowserForPath(
          path,
          factory
        ) as FileBrowser;
        const { services } = browserForPath.model.manager;
        const item = await services.contents.get(path, {
          content: false
        });
        if (trailingSlash && item.type !== 'directory') {
          return showErrorMessage(
            trans.__('Cannot open'),
            new Error(`Path ${path}/ is not a directory`)
          );
        }
        await commands.execute(CommandIDs.goToPath, {
          path,
          dontShowBrowser: args.dontShowBrowser
        });
        if (item.type === 'directory') {
          return;
        }
        return commands.execute('docmanager:open', { path });
      } catch (reason) {
        if (reason.response && reason.response.status === 404) {
          reason.message = trans.__('Could not find path: %1', path);
        }
        return showErrorMessage(trans.__('Cannot open'), reason);
      }
    }
  });
  // Add the openPath command to the command palette
  if (commandPalette) {
    commandPalette.addItem({
      command: CommandIDs.openPath,
      category: trans.__('File Operations')
    });
  }

  commands.addCommand(CommandIDs.open, {
    execute: args => {
      const factory = (args['factory'] as string) || void 0;
      const widget = tracker.currentWidget;

      if (!widget) {
        return;
      }

      const { contents } = widget.model.manager.services;
      return Promise.all(
        toArray(
          map(widget.selectedItems(), item => {
            if (item.type === 'directory') {
              const localPath = contents.localPath(item.path);
              return widget.model.cd(`/${localPath}`);
            }

            return commands.execute('docmanager:open', {
              factory: factory,
              path: item.path
            });
          })
        )
      );
    },
    icon: args => {
      const factory = (args['factory'] as string) || void 0;
      if (factory) {
        // if an explicit factory is passed...
        const ft = registry.getFileType(factory);
        // ...set an icon if the factory name corresponds to a file type name...
        // ...or leave the icon blank
        return ft?.icon?.bindprops({ stylesheet: 'menuItem' });
      } else {
        return folderIcon.bindprops({ stylesheet: 'menuItem' });
      }
    },
    // FIXME-TRANS: Is this localizable?
    label: args =>
      (args['label'] || args['factory'] || trans.__('Open')) as string,
    mnemonic: 0
  });

  commands.addCommand(CommandIDs.openBrowserTab, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (!widget) {
        return;
      }

      return Promise.all(
        toArray(
          map(widget.selectedItems(), item => {
            return commands.execute('docmanager:open-browser-tab', {
              path: item.path
            });
          })
        )
      );
    },
    icon: addIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Open in New Browser Tab'),
    mnemonic: 0
  });

  commands.addCommand(CommandIDs.copyDownloadLink, {
    execute: () => {
      const widget = tracker.currentWidget;
      if (!widget) {
        return;
      }

      return widget.model.manager.services.contents
        .getDownloadUrl(widget.selectedItems().next()?.path ?? '/')
        .then(url => {
          Clipboard.copyToSystem(url);
        });
    },
    icon: copyIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Copy Download Link'),
    mnemonic: 0
  });

  commands.addCommand(CommandIDs.paste, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.paste();
      }
    },
    icon: pasteIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Paste'),
    mnemonic: 0
  });

  commands.addCommand(CommandIDs.createNewDirectory, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.createNewDirectory();
      }
    },
    icon: newFolderIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('New Folder')
  });

  /**
   * Changes: Path definition was changed to get a correct path from registered widget - also marked in code block
   */
  commands.addCommand(CommandIDs.createNewFile, {
    execute: () => {
      void commands.execute('docmanager:new-untitled', {
        path: tracker.currentWidget?.model.path.toString(), // Path definition was changed to get a correct path from registered widget
        type: 'file',
        ext: 'txt'
      });
    },
    icon: textEditorIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('New File')
  });

  /**
   * Changes: Path definition was changed to get a correct path from registered widget - also marked in code block
   */
  commands.addCommand(CommandIDs.createNewMarkdownFile, {
    execute: () => {
      void commands.execute('docmanager:new-untitled', {
        path: tracker.currentWidget?.model.path.toString(), // Path definition was changed to get a correct path from registered widget
        type: 'file',
        ext: 'md'
      });
    },
    icon: markdownIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('New Markdown File')
  });

  commands.addCommand(CommandIDs.rename, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.rename();
      }
    },
    icon: editIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Rename'),
    mnemonic: 0
  });

  commands.addCommand(CommandIDs.copyPath, {
    execute: () => {
      const widget = tracker.currentWidget;
      if (!widget) {
        return;
      }
      const item = widget.selectedItems().next();
      if (!item) {
        return;
      }

      Clipboard.copyToSystem(item.path);
    },
    isVisible: () =>
      !!tracker.currentWidget &&
      tracker.currentWidget.selectedItems().next !== undefined,
    icon: fileIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Copy Path')
  });

  commands.addCommand(CommandIDs.showBrowser, {
    execute: args => {
      const path = (args.path as string) || '';
      const browserForPath = Private.getBrowserForPath(path, factory);

      // Check for browser not found
      if (!browserForPath) {
        return;
      }
      // Shortcut if we are using the main file browser
      if (browser === browserForPath) {
        labShell.activateById(browser.id);
        return;
      } else {
        const areas: ILabShell.Area[] = ['left', 'right'];
        for (const area of areas) {
          const it = labShell.widgets(area);
          let widget = it.next();
          while (widget) {
            if (widget.contains(browserForPath)) {
              labShell.activateById(widget.id);
              return;
            }
            widget = it.next();
          }
        }
      }
    }
  });

  commands.addCommand(CommandIDs.shutdown, {
    execute: () => {
      const widget = tracker.currentWidget;

      if (widget) {
        return widget.shutdownKernels();
      }
    },
    icon: stopIcon.bindprops({ stylesheet: 'menuItem' }),
    label: trans.__('Shut Down Kernel')
  });

  commands.addCommand(CommandIDs.toggleBrowser, {
    execute: () => {
      if (browser.isHidden) {
        return commands.execute(CommandIDs.showBrowser, void 0);
      }

      return commands.execute(CommandIDs.hideBrowser, void 0);
    }
  });

  commands.addCommand(CommandIDs.createLauncher, {
    label: trans.__('New Launcher'),
    execute: () => createLauncher(commands, browser)
  });

  commands.addCommand(CommandIDs.toggleNavigateToCurrentDirectory, {
    label: trans.__('Show Active File in File Browser'),
    isToggled: () => browser.navigateToCurrentDirectory,
    execute: () => {
      const value = !browser.navigateToCurrentDirectory;
      const key = 'navigateToCurrentDirectory';
      return settingRegistry
        .set('@jupyterlab/filebrowser-extension:browser', key, value)
        .catch(() => {
          console.error('Failed to set navigateToCurrentDirectory setting');
        });
    }
  });

  commands.addCommand(CommandIDs.toggleLastModified, {
    label: trans.__('Toggle Last Modified Column'),
    execute: () => {
      const header = DOMUtils.findElement(document.body, 'jp-id-modified');
      const column = DOMUtils.findElements(
        document.body,
        'jp-DirListing-itemModified'
      );
      if (header.classList.contains('jp-LastModified-hidden')) {
        header.classList.remove('jp-LastModified-hidden');
        for (let i = 0; i < column.length; i++) {
          column[i].classList.remove('jp-LastModified-hidden');
        }
      } else {
        header.classList.add('jp-LastModified-hidden');
        for (let i = 0; i < column.length; i++) {
          column[i].classList.add('jp-LastModified-hidden');
        }
      }
    }
  });

  commands.addCommand(CommandIDs.search, {
    label: trans.__('Search on File Names'),
    execute: () => alert('search')
  });

  if (mainMenu) {
    mainMenu.settingsMenu.addGroup(
      [{ command: CommandIDs.toggleNavigateToCurrentDirectory }],
      5
    );
  }

  if (commandPalette) {
    commandPalette.addItem({
      command: CommandIDs.toggleNavigateToCurrentDirectory,
      category: trans.__('File Operations')
    });
  }

  /**
   * A menu widget that dynamically populates with different widget factories
   * based on current filebrowser selection.
   */
  class OpenWithMenu extends Menu {
    protected onBeforeAttach(msg: Message): void {
      // clear the current menu items
      this.clearItems();

      // get the widget factories that could be used to open all of the items
      // in the current filebrowser selection
      const factories = tracker.currentWidget
        ? OpenWithMenu._intersection(
            map(tracker.currentWidget.selectedItems(), i => {
              return OpenWithMenu._getFactories(i);
            })
          )
        : undefined;

      if (factories) {
        // make new menu items from the widget factories
        factories.forEach(factory => {
          this.addItem({
            args: { factory: factory },
            command: CommandIDs.open
          });
        });
      }

      super.onBeforeAttach(msg);
    }

    static _getFactories(item: Contents.IModel): Array<string> {
      const factories = registry
        .preferredWidgetFactories(item.path)
        .map(f => f.name);
      const notebookFactory = registry.getWidgetFactory('notebook')?.name;
      if (
        notebookFactory &&
        item.type === 'notebook' &&
        factories.indexOf(notebookFactory) === -1
      ) {
        factories.unshift(notebookFactory);
      }

      return factories;
    }

    static _intersection<T>(iter: IIterator<Array<T>>): Set<T> | void {
      // pop the first element of iter
      const first = iter.next();
      // first will be undefined if iter is empty
      if (!first) {
        return;
      }

      // "initialize" the intersection from first
      const isect = new Set(first);
      // reduce over the remaining elements of iter
      return reduce(
        iter,
        (isect, subarr) => {
          // filter out all elements not present in both isect and subarr,
          // accumulate result in new set
          return new Set(subarr.filter(x => isect.has(x)));
        },
        isect
      );
    }
  }

  // matches anywhere on filebrowser
  const selectorContent = '.jp-DirListing-content';
  // matches all filebrowser items
  const selectorItem = '.jp-DirListing-item[data-isdir]';
  // matches only non-directory items
  const selectorNotDir = '.jp-DirListing-item[data-isdir="false"]';

  // If the user did not click on any file, we still want to show paste and new folder,
  // so target the content rather than an item.
  app.contextMenu.addItem({
    command: CommandIDs.createNewDirectory,
    selector: selectorContent,
    rank: 1
  });

  app.contextMenu.addItem({
    command: CommandIDs.createNewFile,
    selector: selectorContent,
    rank: 2
  });

  app.contextMenu.addItem({
    command: CommandIDs.createNewMarkdownFile,
    selector: selectorContent,
    rank: 3
  });

  app.contextMenu.addItem({
    command: CommandIDs.paste,
    selector: selectorContent,
    rank: 4
  });

  app.contextMenu.addItem({
    command: CommandIDs.open,
    selector: selectorItem,
    rank: 1
  });

  const openWith = new OpenWithMenu({ commands });
  openWith.title.label = trans.__('Open With');
  app.contextMenu.addItem({
    type: 'submenu',
    submenu: openWith,
    selector: selectorNotDir,
    rank: 2
  });

  app.contextMenu.addItem({
    command: CommandIDs.openBrowserTab,
    selector: selectorNotDir,
    rank: 3
  });

  app.contextMenu.addItem({
    command: CommandIDs.rename,
    selector: selectorItem,
    rank: 4
  });
  app.contextMenu.addItem({
    command: CommandIDs.del,
    selector: selectorItem,
    rank: 5
  });
  app.contextMenu.addItem({
    command: CommandIDs.cut,
    selector: selectorItem,
    rank: 6
  });

  app.contextMenu.addItem({
    command: CommandIDs.copy,
    selector: selectorNotDir,
    rank: 7
  });

  app.contextMenu.addItem({
    command: CommandIDs.duplicate,
    selector: selectorNotDir,
    rank: 8
  });
  app.contextMenu.addItem({
    command: CommandIDs.download,
    selector: selectorNotDir,
    rank: 9
  });
  app.contextMenu.addItem({
    command: CommandIDs.shutdown,
    selector: selectorNotDir,
    rank: 10
  });

  app.contextMenu.addItem({
    command: CommandIDs.share,
    selector: selectorItem,
    rank: 11
  });
  app.contextMenu.addItem({
    command: CommandIDs.copyPath,
    selector: selectorItem,
    rank: 12
  });
  app.contextMenu.addItem({
    command: CommandIDs.copyDownloadLink,
    selector: selectorNotDir,
    rank: 13
  });
  app.contextMenu.addItem({
    command: CommandIDs.toggleLastModified,
    selector: '.jp-DirListing-header',
    rank: 14
  });
}

/**
 * Restores file browser state and overrides state if tree resolver resolves.
 * Copied from packages/filebrowser-extension/src/index.ts:1196
 * Extracted from Private namespace
 */
export async function restoreBrowser(
  browser: FileBrowser,
  commands: CommandRegistry,
  router: IRouter | null,
  tree: JupyterFrontEnd.ITreeResolver | null
): Promise<void> {
  const restoring = 'jp-mod-restoring';

  browser.addClass(restoring);

  if (!router) {
    await browser.model.restore(browser.id);
    await browser.model.refresh();
    browser.removeClass(restoring);
    return;
  }

  const listener = async () => {
    router.routed.disconnect(listener);

    const paths = await tree?.paths;
    if (paths?.file || paths?.browser) {
      // Restore the model without populating it.
      await browser.model.restore(browser.id, false);
      if (paths.file) {
        await commands.execute(CommandIDs.openPath, {
          path: paths.file,
          dontShowBrowser: true
        });
      }
      if (paths.browser) {
        await commands.execute(CommandIDs.openPath, {
          path: paths.browser,
          dontShowBrowser: true
        });
      }
    } else {
      await browser.model.restore(browser.id);
      await browser.model.refresh();
    }
    browser.removeClass(restoring);
  };
  router.routed.connect(listener);
}

/**
 * Create a launcher for a given filebrowser widget.
 * Copied from packages/filebrowser-extension/src/index.ts:1196
 * Added export, extracted from Private namespace
 */
export function createLauncher(
  commands: CommandRegistry,
  browser: FileBrowser
): Promise<MainAreaWidget<Launcher>> {
  const { model } = browser;

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
}

/**
 * A namespace for private module data.
 * Copied from packages/filebrowser-extension/src/index.ts:1113
 * (not everything from namespace has been imported)
 */
namespace Private {
  /**
   * Navigate to a path or the path containing a file.
   * Copied from packages/filebrowser-extension/src/index.ts:1168
   */
  export async function navigateToPath(
    path: string,
    factory: IFileBrowserFactory,
    translator: ITranslator
  ): Promise<Contents.IModel> {
    const trans = translator.load('jupyterlab');
    const browserForPath = Private.getBrowserForPath(path, factory);
    if (!browserForPath) {
      throw new Error(trans.__('No browser for path'));
    }
    const { services } = browserForPath.model.manager;
    const localPath = services.contents.localPath(path);

    await services.ready;
    const item = await services.contents.get(path, { content: false });
    const { model } = browserForPath;
    await model.restored;
    if (item.type === 'directory') {
      await model.cd(`/${localPath}`);
    } else {
      await model.cd(`/${PathExt.dirname(localPath)}`);
    }
    return item;
  }

  /**
   * Get browser object given file path.
   * Copied from packages/filebrowser-extension/src/index.ts:1138
   */
  export function getBrowserForPath(
    path: string,
    factory: IFileBrowserFactory
  ): FileBrowser | undefined {
    const { defaultBrowser: browser, tracker } = factory;
    const driveName = browser.model.manager.services.contents.driveName(path);

    if (driveName) {
      const browserForPath = tracker.find(
        _path => _path.model.driveName === driveName
      );

      if (!browserForPath) {
        // warn that no filebrowser could be found for this driveName
        console.warn(
          `${CommandIDs.goToPath} failed to find filebrowser for path: ${path}`
        );
        return;
      }

      return browserForPath;
    }

    // if driveName is empty, assume the main filebrowser
    return browser;
  }
}
