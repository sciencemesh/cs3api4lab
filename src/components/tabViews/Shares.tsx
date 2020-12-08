import React, {useState, useEffect} from 'react';

type SharesProps = {
    grantees: Map<string, string>
}

const Shares = (props :SharesProps) :JSX.Element => {
    const [grantees] = useState(props.grantees);
    const [granteesList, setGranteesList] = useState([]);

    const refresh = (grantees :Map<string,string>) :void => {
        const granteesListArr :Array<Object> = [];
        grantees.forEach(((permission, grantee) => {
            granteesListArr.push(<div className='jp-shares-element' key={grantee}>
                <div className='jp-shares-owner'>{grantee}</div>
                <div className='jp-shares-label'>
                <span className={permission}>{permission}</span>
                </div>
            </div>);
        }));

        setGranteesList(granteesListArr);
    }

    useEffect(() => {
        refresh(grantees)
    }, [grantees]);

    const showedValues = (event :React.ChangeEvent<HTMLInputElement>) :void => {
        const granteesFiltered = new Map(grantees);
        granteesFiltered.forEach( (permission, grantee) => {
            if (grantee.toString().search(event.target.value.toString()) == -1) {
                granteesFiltered.delete(grantee);
            }
        });

        refresh(granteesFiltered);
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
