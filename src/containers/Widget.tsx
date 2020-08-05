import { ReactWidget } from '@jupyterlab/apputils';
import React from 'react';

import Main from "./Main";

/**
 * Widget container.
 */
export class Widget extends ReactWidget {
    constructor() {
        super();
        this.addClass('jp-ReactWidget');
    }

    protected render(): JSX.Element {
      return (
          <Main />
      )
    }
}


