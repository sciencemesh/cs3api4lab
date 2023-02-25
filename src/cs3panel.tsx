import { BoxLayout, BoxPanel, DockPanel, Widget } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';
import { LabIcon } from '@jupyterlab/ui-components';
import { IStateDB } from '@jupyterlab/statedb';
import { BottomProps } from './types';
import { useState } from 'react';
import { FileBrowser } from '@jupyterlab/filebrowser';
import { IIterator } from '@lumino/algorithm';
import { ISignal, Signal } from '@lumino/signaling';

export class Cs3Panel extends Widget {
  protected header: BoxPanel;
  protected main: DockPanel;
  protected bottom: BoxPanel;
  private _sharesTabVisible = new Signal<Widget, any>(this);
  private _filesTabVisible = new Signal<Widget, any>(this);

  constructor(
    title: string,
    id: string,
    icon: LabIcon,
    options: Widget.IOptions = {},
    stateDB: IStateDB
  ) {
    super(options);

    this.id = id;
    this.title.caption = title;
    this.title.icon = icon;

    const rootLayout = new BoxLayout();
    rootLayout.direction = 'top-to-bottom';
    rootLayout.spacing = 0;

    this.header = new BoxPanel();
    this.bottom = new BoxPanel();

    this.header.direction = 'left-to-right';
    this.bottom.direction = 'left-to-right';

    this.header.addClass('c3-panel-header');
    this.bottom.addClass('c3-panel-bottom');

    this.header.id = 'cs3-dock-panel-header';
    this.bottom.id = 'cs3-dock-panel-bottom';

    this.main = new DockPanel();
    this.main.tabsMovable = false;
    this.main.tabsConstrained = false;
    this.main.id = 'cs3-dock-panel-main';
    this.main.title.iconClass = 'cs3-dock-panel';
    this.main.title.caption = title;
    this.main.spacing = 1;

    BoxLayout.setStretch(this.header, 2);
    BoxLayout.setStretch(this.main, 32);
    BoxLayout.setStretch(this.bottom, 1);

    BoxLayout.setVerticalAlignment(this.header, 'center');
    BoxLayout.setVerticalAlignment(this.bottom, 'center');

    rootLayout.addWidget(this.header);
    rootLayout.addWidget(this.main);
    rootLayout.addWidget(this.bottom);

    this.layout = rootLayout;

    // detect which tab is opened to limit calls
    this.main.layoutModified.connect((dockPanel): void => {
      if (dockPanel.layout !== null) {
        const dockPanelIterator: IIterator<Widget> = dockPanel.layout.iter();
        let tab: Widget | undefined;
        do {
          tab = dockPanelIterator?.next();
          if (tab !== undefined && Cs3Panel.isWidgetVisible(tab)) {
            if (tab.id === 'cs3filebrowser') {
              this._filesTabVisible.emit(this);
              this.bottom.show();
            }
            if (tab.id === 'sharesPanel') {
              // emit signal to refresh the tab
              this._sharesTabVisible.emit(this);
              this.bottom.hide();
            }
            void stateDB.save('activeTab', tab.id);
          }
        } while (tab);
      }
    });
  }

  public addTab(widget: Widget, options: DockPanel.IAddOptions = {}): void {
    this.main.addWidget(widget, options);
  }

  public addHeader(widget: Widget): void {
    this.header.addWidget(widget);
  }

  public addBottom(widget: Widget): void {
    this.bottom.addWidget(widget);
  }

  private static isWidgetVisible(widget: Widget): boolean {
    if (widget === undefined) {
      return false;
    }
    return widget.isVisible;
  }

  public sharesTabVisible(): ISignal<Widget, any> {
    return this._sharesTabVisible;
  }

  public filesTabVisible(): ISignal<Widget, any> {
    return this._filesTabVisible;
  }
}

export class Cs3HeaderWidget extends ReactWidget {
  constructor(title: string, id: string, options: Widget.IOptions = {}) {
    super(options);
    this.addClass('c3-header-widget');
    this.id = id;
    this.title.label = title;
    this.title.caption = title;
    this.title.closable = false;
  }

  protected render(): JSX.Element {
    return <h1>{this.title.caption}</h1>;
  }
}

export const Bottom = (props: BottomProps): JSX.Element => {
  // const [text, setText] = useState('');
  const [hiddenFiles, setHiddenFiles] = useState(0);
  const [action, setAction] = useState('show');

  const setLabel = async (): Promise<void> => {
    const showHidden: boolean = (await props.db.fetch('showHidden')) as boolean;
    const hiddenFilesNo: number =
      ((await props.db.fetch('hiddenFilesNo')) as number) || 0;
    const action = showHidden === undefined || !showHidden ? 'show' : 'hide';
    setHiddenFiles(hiddenFilesNo);
    setAction(action);
  };

  props.browser.model.pathChanged.connect(async () => {
    await setLabel();
  });

  props.browser.model.refreshed.connect(async () => {
    await setLabel();
  });

  return (
    <div className={'jp-bottom-div'}>
      <div className="jp-bottom-hidden-files">
        {hiddenFiles} hidden files (<a>{action}</a>)
      </div>
    </div>
  );
};

export class Cs3BottomWidget extends ReactWidget {
  private bottomProps: {
    db: IStateDB;
    browser: FileBrowser;
  };

  constructor(
    title: string,
    id: string,
    options: Widget.IOptions = {},
    stateDB: IStateDB,
    browser: FileBrowser
  ) {
    super(options);
    // this.addClass('c3-bottom-widget');
    // this.addClass('p-Widget');
    this.id = id;
    this.title.closable = false;
    this.bottomProps = { db: stateDB, browser: browser };
    this.node.onclick = async () => {
      const showHidden = await stateDB.fetch('showHidden');
      await stateDB.save('showHidden', !showHidden);
      await browser.model.refresh();
    };
  }

  protected render(): JSX.Element {
    return (
      <Bottom db={this.bottomProps.db} browser={this.bottomProps.browser} />
    );
  }
}

export class Cs3TabWidget extends ReactWidget {
  constructor(title: string, icon?: LabIcon, options: Widget.IOptions = {}) {
    super(options);
    this.addClass('c3-tab-widget');

    this.title.label = title;
    this.title.caption = title;
    this.title.className = 'jp-main-tab';
    this.title.iconClass = 'jp-main-tab-icon';
    if (icon) {
      this.title.icon = icon;
    }
  }

  protected render(): JSX.Element {
    return <div>{this.title.caption}</div>;
  }
}
