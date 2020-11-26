// import {Contents} from "@jupyterlab/services";
import {requestAPI} from './services/requestAPI';
import {IStateDB} from '@jupyterlab/statedb';
import { ReadonlyJSONObject } from '@lumino/coreutils';

export async function CS3ContainerFiles(stateDB: IStateDB, path: string = null) :Promise<any> {
    let share = await stateDB.fetch('share');
    const shareType = (share as ReadonlyJSONObject)['share_type']

    let fileList = null;
    switch (shareType) {
        case 'by_me':
            fileList = await getSharedByMe();
            break;
        case 'with_me':
            fileList = await getSharedWithMe();
            break;
        case 'filelist':
        default:
            fileList = await getFileList(path);
    }

    return fileList;
}

export async function CS3Rename(oldLocalPath: string, newLocalPath: string) {
    // requestAPI('/api/contents/' + oldLocalPath, {
    //     method: 'PATCH',
    //     body: {
    //         path: newLocalPath
    //     }
    // })
}

async function getFileList(path: string): Promise<any> {
    return await requestAPI('/api/contents/' + path, {
        method: 'get',
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
