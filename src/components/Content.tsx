import React from 'react';
import {Contents} from "@jupyterlab/services";
import Info from "./tabViews/Info";
import Shares from "./tabViews/Shares";

type ContentProps = {
    content: Contents.IModel,
    contentType: string,
    grantees: Object
}


const Content = (props: ContentProps): JSX.Element => {
    let elementToDisplay :JSX.Element;

    switch (props.contentType) {
        case 'shares': elementToDisplay = Shares({grantees: props.grantees});
            break;

        case 'info':
        default:
            elementToDisplay = Info({ content: props.content});
    }

    return (
        <div className='jp-file-info-content'>
            {elementToDisplay}
        </div>
    );
}

export default Content;
