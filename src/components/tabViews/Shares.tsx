import React, {useState, useEffect} from 'react';
// import {Contents} from "@jupyterlab/services";
// import searchIcon from '@jupyterlab/ui-components';

// import {requestAPI} from "../../services/requestAPI"

type SharesProps = {
    grantees: Object
}

const Shares = (props :SharesProps) :JSX.Element => {
    const [grantees, setGrantees] = useState(new Map(Object.entries(props.grantees)));
    const granteesList :Array<object> = [];

    const refresh = (granteesList :Array<object>) :void => {
        grantees.forEach((permision, grantee) => {
            const label :string = (permision == 'viewer') ? 'label read-label' : 'label write-label';

            granteesList.push(<div className='jp-shares-element' key={grantee}>
                <div className='jp-shares-owner'>{grantee}</div>
                <div className='jp-shares-label'>
                    <span className={label}>{permision}</span>
                </div>
            </div>);
        });
        console.log('1',granteesList);
    }

    console.log('2', granteesList);

    useEffect(() => {
        console.log('refresh grantee')
        refresh(granteesList)
    }, [grantees]);

    const showedValues = (event :React.ChangeEvent<HTMLInputElement>) :void => {
        console.log('showed values changed')

        grantees.forEach( (permission, grantee) => {
            if (grantee.toString().search(event.target.value.toString()) == -1) {
                grantees.delete(grantee);
            }
        });

        setGrantees(grantees);
    };

    return (
        <div className='jp-shares'>
            <div className='jp-shares-search-container'>
                <input type='text' className='jp-shares-search' onChange={showedValues}/>
            </div>

            <div className='jp-shares-list-container'>
                {
                    granteesList.map((grantee) => {
                        return grantee;
                    })
                }
            </div>
        </div>
    );
}

export default Shares;
