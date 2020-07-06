import React from 'react';

type ResultProps = {
    message: string;
}

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

export default Results;