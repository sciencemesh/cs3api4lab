import {requestAPI} from './services/requestAPI';
import {IStateDB} from '@jupyterlab/statedb';
import { ReadonlyJSONObject } from '@lumino/coreutils';
import {Contents} from "@jupyterlab/services";

export async function CS3ContainerFiles(stateDB: IStateDB, path: string = null, options :Contents.IFetchOptions = null) :Promise<any> {
    let share = await stateDB.fetch('share');
    const shareType = (share as ReadonlyJSONObject)['share_type']

    if (path != '') {
        return await getFileList(path, options);
    }

    switch (shareType) {
        case 'by_me':
            return await getSharedByMe();
        case 'with_me':
            return await getSharedWithMe();
        case 'filelist':
        default:
            return await getFileList(path, options);
    }
}

async function getFileList(path: string, options :Contents.IFetchOptions): Promise<any> {
    const {type, format, content} = options;

    let url :string = '';
        url += '?content=' + (content  ? 1 : 0);
    if (type)
        url += '&type=' + type;
    if (format && type != 'notebook')
        url += '&format=' + format;

    return await requestAPI('/api/contents/' + path + ''  + url, {
        method: 'get'
    });
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
