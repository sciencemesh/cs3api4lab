import {Contents} from "@jupyterlab/services";
import {requestAPI} from './services/requestAPI';
import {IStateDB} from '@jupyterlab/statedb';
import { ReadonlyJSONObject } from '@lumino/coreutils';

export async function getDummyFilesForCS3Share(stateDB: IStateDB) :Promise<any> {
    let share = await stateDB.fetch('share');
    const share_type = (share as ReadonlyJSONObject)['share_type']

    const shares = (share_type == 'with_me') ? await getSharedWithMe() : await getSharedByMe();
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

    const fileList: Contents.IModel[] = [];
    shares.forEach((x :any) => {
        fileList.push({
            name: x.id.opaque_id,
            path: x.id.opaque_id,
            type: 'file',
            writable: false,
            created: '2020-07-07T08:19:19Z',
            last_modified: '2020-07-07T08:19:19Z',
            content: 'dsa',
            mimetype: 'text/plain',
            format: 'json',
            size: 21,
        });
    });

    return {...contents, content: fileList};
}

export async function getSharedByMe (): Promise<any>{
    const  shares = await requestAPI('/api/cs3test/shares/list', {
        method: 'get'
    });

    return shares;
}

export async function getSharedWithMe (): Promise<any>{
    const  shares = await requestAPI('/api/cs3test/shares/received', {
        method: 'get'
    });

    return shares;
}
