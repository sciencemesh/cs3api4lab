import { ReactWidget } from '@jupyterlab/apputils';
import React from 'react';

import CreateShare from "./CreateShare";

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
          <CreateShare />
      )
    }
}


