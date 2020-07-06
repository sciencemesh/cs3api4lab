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
const Main = (): JSX.Element => {
    const [message, setMessage] = useState(null);

    return (<>
        <ControlPanel makeRequest={async ()=> {
            try {
                const data = await requestAPI<any>('/api/cs3test/helloworld', {
                    method: 'GET'
                });

                setMessage(JSON.stringify(data));
            } catch (e) {
                console.log('request errors', e);
            }
        }}/>

        <Results message={message} />
    </>);
};

export default Main;