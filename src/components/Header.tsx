import React from 'react';
import {Contents} from "@jupyterlab/services";

import {findFileIcon} from "../services/findFileIcon";

type HeaderProps = {
    fileInfo: Contents.IModel
}

const Header = (props :HeaderProps) :JSX.Element => {
    const Icon = findFileIcon(props.fileInfo);

    return (
        <div className='jp-file-info-header'>
            <Icon.react className='jp-file-info-header-icon' />
            <div className='file-info-header-title'>
                {props.fileInfo.name}
            </div>
        </div>
    );
}

export default Header;
