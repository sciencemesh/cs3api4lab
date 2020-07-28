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
                <table>
                    <tbody>
                    <tr><td>{}</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default Shares;
