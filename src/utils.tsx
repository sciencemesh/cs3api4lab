import { FileBrowser } from '@jupyterlab/filebrowser';
import { Cs3TitleWidget } from './cs3panel';
import { BoxLayout, BoxPanel } from '@lumino/widgets';
import { ILabShell, JupyterFrontEnd } from '@jupyterlab/application';
import { MainAreaWidget, ToolbarButton } from '@jupyterlab/apputils';
import { addIcon } from '@jupyterlab/ui-components';
import { Launcher } from '@jupyterlab/launcher';

export function createShareBox(
  id: string,
  title: string,
  fileWidget: FileBrowser
) {
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

export function addLaunchersButton(
  app: JupyterFrontEnd<JupyterFrontEnd.IShell>,
  fileBrowser: FileBrowser,
  labShell: ILabShell
) {
  const { commands } = app;
  const { model } = fileBrowser;

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

    fileBrowser.toolbar.insertItem(0, 'launch', launcher);
  }
}
