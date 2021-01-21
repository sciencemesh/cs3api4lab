import {ReactWidget} from '@jupyterlab/apputils';
import React, {useState} from 'react';
import {Contents} from "@jupyterlab/services";
import {requestAPI} from "./services";
import {CreateShareProps, ResultProps, ShareFormProps, WidgetProps} from "./types";


/**
 * Request results panel.
 *
 * @param props
 *
 * @constructor
 */
const Results = (props: ResultProps): JSX.Element => {
    return (
        <div className='resultWindow'>
            <pre>
                {props.message}
            </pre>
        </div>
    );
}


/**
 * Share form widget.
 *
 * @param props
 *
 * @constructor
 */
const ShareForm = (props: ShareFormProps): JSX.Element => {
    const [formValues, setFormState] = useState({
        endpoint: '/',
        file_path: '/home/' + props.fileInfo.path.replace('cs3drive:', ''),
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
        <div className='ShareForm'>
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

/**
 * Main container.
 *
 * @constructor
 */
const CreateShare = (props: CreateShareProps): JSX.Element => {
    const [message, setMessage] = useState(null);

    return (<>
        <ShareForm fileInfo={props.fileInfo}
                      makeRequest={async (params: object) => {
                          try {
                              const data = await requestAPI<any>('/api/cs3/shares', {
                                  method: 'POST',
                                  body: JSON.stringify(params)
                              });

                              setMessage(JSON.stringify(data));
                          } catch (e) {
                              console.log('request errors', e);
                          }
                      }}

        />

        <Results message={message} />
    </>);
};


/**
 * ShareWidget container.
 */
export class ShareWidget extends ReactWidget {
    private readonly fileInfo: Contents.IModel;

    constructor(props :WidgetProps) {
        super();
        this.addClass('jp-ReactWidget');
        this.fileInfo = props.fileInfo;
    }

    protected render(): JSX.Element {
        return (
            <CreateShare fileInfo={this.fileInfo}/>
        )
    }
}




