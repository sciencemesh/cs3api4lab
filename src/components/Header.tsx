import React from 'react';
import {Contents} from "@jupyterlab/services";
import {LabIcon} from "@jupyterlab/ui-components";

type HeaderProps = {
    fileInfo: Contents.IModel
}

const Header = (props :HeaderProps) :JSX.Element => {
    const Icon = LabIcon.resolve({
        icon: 'ui-components:image'
    });
    console.log(props.fileInfo.format);
    return (<div className='jp-file-info-header'>
        <Icon.react className='jp-file-info-header-icon' />
        <div className='file-info-header-title'>
            HEADER!!!!
        </div>
    </div>);
}

export default Header;
