import { Widget } from '@lumino/widgets';
import { DockPanel } from '@lumino/widgets';
import { BoxLayout } from '@lumino/widgets';
import { BoxPanel } from '@lumino/widgets';
import { ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';
import {LabIcon} from "@jupyterlab/ui-components";

export class Cs3Panel extends Widget {
  protected header: BoxPanel;
  protected main: DockPanel;
  protected bottom: BoxPanel;

  constructor(title: string, id: string, icon: LabIcon, options: Widget.IOptions = {}) {
    super(options);

    this.id = id;
    this.title.caption = title;
    this.title.icon = icon;

    const rootLayout = new BoxLayout();
    rootLayout.direction = 'top-to-bottom';
    rootLayout.spacing = 5;

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
  }

  public addTab(widget: Widget, options: DockPanel.IAddOptions = {}) {
    this.main.addWidget(widget, options);
  }

  public addHeader(widget: Widget) {
    this.header.addWidget(widget);
  }

  public addBottom(widget: Widget) {
    this.bottom.addWidget(widget);
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

  protected render(): React.ReactElement<any> {
    return <h1>{this.title.caption}</h1>;
  }
}

export class Cs3BottomWidget extends ReactWidget {
  constructor(title: string, id: string, options: Widget.IOptions = {}) {
    super(options);
    this.addClass('c3-bottom-widget');
    this.id = id;
    this.title.label = title;
    this.title.caption = title;
    this.title.closable = false;
  }

  protected render(): React.ReactElement<any> {
    return <div>{this.title.caption}</div>;
  }
}

export class Cs3TabWidget extends ReactWidget {
  constructor(title: string, icon: LabIcon, options: Widget.IOptions = {}) {
    super(options);
    this.addClass('c3-tab-widget');

    this.title.label = title;
    this.title.caption = title;
    this.title.icon = icon;
  }

  protected render(): React.ReactElement<any> {
    return <div>{this.title.caption}</div>;
  }
}

export class Cs3TitleWidget extends ReactWidget {
  constructor(options: Widget.IOptions = {}) {
    super(options);
    this.addClass('c3-title-widget');
  }

  protected render(): React.ReactElement<any> {
    return <div>{this.title.caption}</div>;
  }
}
