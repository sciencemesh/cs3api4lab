import {Contents} from "@jupyterlab/services";
import {requestAPI} from './services/requestAPI';
import {IStateDB} from '@jupyterlab/statedb';
import { ReadonlyJSONObject } from '@lumino/coreutils';

export async function getDummyFilesForCS3Share(stateDB: IStateDB) :Promise<any> {
    let share = await stateDB.fetch('share');
    const share_type = (share as ReadonlyJSONObject)['share_type']

    const shares = (share_type == 'with_me') ? await getSharedWithMe() : await getSharedByMe();
    console.log('shares', shares);
    const contents: Contents.IModel = {
        name: 'cs3 shared',
        path: '/',
        type: 'directory',
        writable: false,
        created: '',
        last_modified: '',
        mimetype: '',
        content: null,
        format: 'json'
    };

    const fileList = (typeof shares?.content != 'undefined') ? shares.content : [];
    return {...contents, content: fileList};
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
