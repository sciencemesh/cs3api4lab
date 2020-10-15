import {requestAPI} from './services/requestAPI';
import {IStateDB} from '@jupyterlab/statedb';
import { ReadonlyJSONObject } from '@lumino/coreutils';

export async function getDummyFilesForCS3Share(stateDB: IStateDB) :Promise<any> {
    let share = await stateDB.fetch('share');
    const shareType = (share as ReadonlyJSONObject)['share_type']

    const shares = (shareType == 'with_me') ? await getSharedWithMe() : await getSharedByMe();
    return shares;
}

async function getSharedByMe(): Promise<any>{
    return await requestAPI('/api/cs3/shares/list', {
        method: 'get'
    });
}

async function getSharedWithMe(): Promise<any>{
    return await requestAPI('/api/cs3/shares/received', {
        method: 'get'
    });
}
