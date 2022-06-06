import { FileBrowser } from '@jupyterlab/filebrowser';
import { Cs3TitleWidget } from './cs3panel';
import { BoxLayout, BoxPanel } from '@lumino/widgets';
import { ILabShell, JupyterFrontEnd } from '@jupyterlab/application';
import { MainAreaWidget, ToolbarButton } from '@jupyterlab/apputils';
import { addIcon, folderIcon } from '@jupyterlab/ui-components';
import { Launcher } from '@jupyterlab/launcher';
import { IStateDB } from '@jupyterlab/statedb';

export function createShareBox(
  id: string,
  title: string,
  fileWidget: FileBrowser
): BoxPanel {
  const titleWidget = new Cs3TitleWidget();
  titleWidget.title.caption = title;
  titleWidget.id = id + '-title';
  titleWidget.addClass('c3-title-widget');

  const boxPanel = new BoxPanel();
  boxPanel.direction = 'top-to-bottom';
  boxPanel.spacing = 5;
  boxPanel.id = id + '-box-panel';

  boxPanel.addWidget(titleWidget);
  boxPanel.addWidget(fileWidget);

  BoxLayout.setStretch(titleWidget, 1);
  BoxLayout.setStretch(fileWidget, 16);

  return boxPanel;
}

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
          void fileBrowser.model.cd(homeDir);
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
