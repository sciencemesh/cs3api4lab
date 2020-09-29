import React, {useState} from 'react';

// Services
import {requestAPI} from "../services/requestAPI";

// components
import ControlPanel from "../components/ControlPanel";
import Results from "../components/Results";
import {Contents} from "@jupyterlab/services";


type CreateShareProps = {
    fileInfo: Contents.IModel;
}

/**
 * Main container.
 *
 * @constructor
 */
const CreateShare = (props: CreateShareProps): JSX.Element => {
    const [message, setMessage] = useState(null);

    return (<>
        <ControlPanel fileInfo={props.fileInfo}
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

export default CreateShare;
