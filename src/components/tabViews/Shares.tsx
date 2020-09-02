import React from 'react';
// import searchIcon from '@jupyterlab/ui-components';

// import {requestAPI} from "../../services/requestAPI";

// const getShares = async () => {
//     let data :Promise<object> = null;
//     try {
//         data = await requestAPI<any>('/api/cs3test/shares/file?file_id=test.txt', {
//             method: 'GET',
//         });
//     } catch (error) {
//         console.log(error);
//     }
//
//     return data;
// }

const Shares = () :JSX.Element => {
    // const [personList, setPersonList] = useState({});
    // setPersonList({
    //     test: 'test'
    // });


    // shares.then( (value :any) => {
    //     // setPersonList(value);
    //     console.log(value);
    // });
    // console.log(personList);

    return (
        <div className='jp-shares'>
            <div className='jp-shares-search-container'>
                <input type='text' className='jp-shares-search'/>
            </div>

            <div className='jp-shares-list-container'>
                <div className='jp-shares-element'>
                    <div className='jp-shares-owner'>Uzytkownik jeden</div>
                    <div className='jp-shares-label'>
                        <span className='label write-label'>Editor</span>
                    </div>
                </div>

                <div className='jp-shares-element'>
                    <div className='jp-shares-owner'>Uzytkownik dwa</div>
                    <div className='jp-shares-label'>
                        <span className='label read-label'>Viewer</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Shares;
