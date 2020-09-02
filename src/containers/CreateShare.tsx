import React, {useState} from 'react';

// Services
import {requestAPI} from "../services/requestAPI";

// components
import ControlPanel from "../components/ControlPanel";
import Results from "../components/Results";

/**
 * Main container.
 *
 * @constructor
 */
const CreateShare = (): JSX.Element => {
    const [message, setMessage] = useState(null);

    return (<>
        <ControlPanel makeRequest={async () => {
            try {
                const data = await requestAPI<any>('/api/cs3test/shares?endpoint=%2F&file_id=%2Fexample1.txt&grantee=f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c&idp=cesnet.cz&role=viewer&grantee_type=user&token=92c172723a1121bc740b4ebac65e9047881ae82f503a15c5', {
                    method: 'POST',
                    // body: JSON.stringify({
                    //     endpoint: '/',
                    //     file_id: 'example1.txt',
                    //     grantee: 'f7fbf8c8-139b-4376-b307-cf0a8c2d0d9c',
                    //     idp: 'cesnet.cz',
                    //     role: 'viewer',
                    //     gratee_type: 'user',
                    // })
                });

                setMessage(JSON.stringify(data));
            } catch (e) {
                console.log('request errors', e);
            }
        }}/>

        <Results message={message} />
    </>);
};

export default CreateShare;
