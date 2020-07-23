import { ReactWidget } from '@jupyterlab/apputils';
import React from 'react';

import Main from "./Main";
import { Contents } from '@jupyterlab/services';
//
type WidgetProps = {
    fileInfo: Contents.IModel,
}

/**
 * Widget container.
 */
export class Widget extends ReactWidget {
    private readonly fileInfo: Contents.IModel;

    constructor(props :WidgetProps) {
        super();
        this.addClass('jp-ReactWidget');
        this.fileInfo = props.fileInfo;
    }

    protected render(): JSX.Element {
      return (
          <Main fileInfo={this.fileInfo}/>
      )
    }
}


