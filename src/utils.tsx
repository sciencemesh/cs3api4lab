import { FileBrowser } from '@jupyterlab/filebrowser';
import { ILabShell, JupyterFrontEnd } from '@jupyterlab/application';
import { MainAreaWidget, ToolbarButton } from '@jupyterlab/apputils';
import { addIcon, folderIcon } from '@jupyterlab/ui-components';
import { Launcher } from '@jupyterlab/launcher';
import { IStateDB } from '@jupyterlab/statedb';

export function addHomeDirButton(
  app: JupyterFrontEnd<JupyterFrontEnd.IShell>,
  fileBrowser: FileBrowser,
  labShell: ILabShell,
  stateDB: IStateDB
): void {
  if (labShell) {
    const homeDirButton = new ToolbarButton({
      icon: folderIcon,
      onClick: async (): Promise<any> => {
        const homeDir = (await stateDB.fetch('homeDir')) as string;
        if (homeDir) {
          void (await fileBrowser.model.cd(homeDir));
        }
      },
      tooltip: 'Go To Home Dir'
    });
    fileBrowser.toolbar.insertItem(4, 'home', homeDirButton);
  }
}

export function addLaunchersButton(
  app: JupyterFrontEnd<JupyterFrontEnd.IShell>,
  fileBrowser: FileBrowser,
  labShell: ILabShell
): void {
  const { commands } = app;
  const { model } = fileBrowser;

  if (labShell) {
    const launcher = new ToolbarButton({
      icon: addIcon,
      onClick: (): Promise<any> => {
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

    fileBrowser.toolbar.insertItem(0, 'launch', launcher);
  }
}
