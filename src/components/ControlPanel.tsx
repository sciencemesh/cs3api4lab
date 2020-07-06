import React from 'react';

/**
 * Type definition for control props.
 */
type ControlProps = {
    makeRequest: () => void;
}

/**
 * Control widget.
 *
 * @param props
 *
 * @constructor
 */
const ControlPanel = (props: ControlProps): JSX.Element => {
    return (
        <div className='controlPanel'>
            <button onClick={props.makeRequest}>Make request</button>
        </div>
    )
}

export default ControlPanel;