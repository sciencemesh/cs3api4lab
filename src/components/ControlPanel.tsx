import React, {useState} from 'react';
import {Contents} from "@jupyterlab/services";

/**
 * Type definition for control props.
 */
type ControlProps = {
    makeRequest: (params :object) => void;
    fileInfo: Contents.IModel;
}

/**
 * Control widget.
 *
 * @param props
 *
 * @constructor
 */
const ControlPanel = (props: ControlProps): JSX.Element => {
    const [formValues, setFormState] = useState({
        endpoint: '/',
        file_id: '/home/' + props.fileInfo.path,
        grantee: '',
        idp: '',
        role: 'viewer',
        grantee_type: 'user'
    });

    const setFormStateFromValues = (param: React.ChangeEvent<HTMLInputElement>|React.ChangeEvent<HTMLSelectElement>) => {
        let tmpFormState :any = {...formValues};
        tmpFormState[param.target.name] = param.target.value;
        setFormState(tmpFormState);
    }

    const localMakeRequest = () => {
        props.makeRequest(formValues)
    }

    return (
        <div className='controlPanel'>
            <div>
                <div>Grantee</div>
                <div>
                    <input type='text' value={formValues.grantee} name='grantee' onChange={setFormStateFromValues}/>
                </div>
            </div>
            <div>
                <div>IDP</div>
                <div>
                    <input type='text' value={formValues.idp} name='idp' onChange={setFormStateFromValues} />
                </div>
            </div>

            <div>
                <div>Role</div>
                <div>
                    <select onChange={setFormStateFromValues} name='role'>
                        <option value='viewer'>Viewer</option>
                        <option value='editor'>Editor</option>
                    </select>
                </div>
            </div>

            {/*<div>*/}
            {/*    <div>Grantee Type</div>*/}
            {/*    <div>*/}
            {/*        <select name='grantee_type' id='grantee_type' onChange={setFormStateFromValues}>*/}
            {/*            <option value='user'>User</option>*/}
            {/*            <option value="group">Group</option>*/}
            {/*        </select>*/}
            {/*    </div>*/}
            {/*</div>*/}

            <button onClick={localMakeRequest}>Make request</button>
        </div>
    )
}

export default ControlPanel;
