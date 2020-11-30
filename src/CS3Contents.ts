import { Contents, ServerConnection } from '@jupyterlab/services';
import { DocumentRegistry } from '@jupyterlab/docregistry';
// import { ISignal } from '@lumino/signaling';
import {getDummyFilesForCS3Share} from './CS3Drive';
import { Signal, ISignal } from '@lumino/signaling';
import {IStateDB} from '@jupyterlab/statedb';

// import {ICheckpointModel, ICreateOptions, IModel} from "@jupyterlab/services/lib/contents";


export class CS3Contents implements Contents.IDrive {
    private _docRegistry: DocumentRegistry;
    private _fileTypeForPath: (path: string) => DocumentRegistry.IFileType;
    private _fileTypeForContentsModel: (model: Partial<Contents.IModel>) => DocumentRegistry.IFileType;
    private _fileChanged = new Signal<this, Contents.IChangedArgs>(this);
    private _isDisposed = false;
    private _state :IStateDB;

    constructor(registry: DocumentRegistry, stateDB: IStateDB) {
        this._docRegistry = registry;

        // Construct a function to make a best-guess IFileType
        // for a given path.
        this._fileTypeForPath = (path: string) => {
            const fileTypes = registry.getFileTypesForPath(path);
            return fileTypes.length === 0
                ? registry.getFileType('text')!
                : fileTypes[0];
        };
        // Construct a function to return a best-guess IFileType
        // for a given contents model.
        this._fileTypeForContentsModel = (model: Partial<Contents.IModel>) => {
            return registry.getFileTypeForModel(model);
        };

        this._state = stateDB;
        console.log(this._docRegistry, this._fileTypeForPath, this._fileTypeForContentsModel);
    }

    refresh() {
        console.log('refresh');
    }

    /**
     * The name of the drive.
     */
    get name(): 'cs3drive' {
        return 'cs3drive';
    }

    /**
     * Server settings (unused for interfacing with Google Drive).
     */
    readonly serverSettings: ServerConnection.ISettings;


    /**
     * Get a file or directory.
     *
     * @param path: The path to the file.
     *
     * @param options: The options used to fetch the file.
     *
     * @returns A promise which resolves with the file content.
     */
    async get(
        path: string,
        options?: Contents.IFetchOptions
    ): Promise<Contents.IModel> {
        console.log('get content');
        const contents = await getDummyFilesForCS3Share(this._state);
        return contents;
    }

    /**
     * A signal emitted when a file operation takes place.
     */
    get fileChanged(): ISignal<this, Contents.IChangedArgs> {
        return this._fileChanged;
    }
    /**
     * Test whether the manager has been disposed.
     */
    get isDisposed(): boolean {
        return this._isDisposed;
    }

    /**h
     * Dispose of the resources held by the manager.
     */
    dispose(): void {
        if (this.isDisposed) {
            return;
        }
        this._isDisposed = true;
        Signal.clearData(this);
    }

    async getDownloadUrl(localPath: string): Promise<string> {
        return new Promise<string>(resolve => { return '/'});
    };

    newUntitled(options?: Contents.ICreateOptions): Promise<Contents.IModel> {
        return getDummyFilesForCS3Share(this._state);
    }

    delete(localPath: string): Promise<void> {
        return new Promise<void>(resolve => {});
    };

    rename(oldLocalPath: string, newLocalPath: string): Promise<Contents.IModel> {
        return getDummyFilesForCS3Share(this._state);
    }
    save(localPath: string, options?: Partial<Contents.IModel>): Promise<Contents.IModel> {
        return getDummyFilesForCS3Share(this._state);
    }

    copy(localPath: string, toLocalDir: string): Promise<Contents.IModel> {
        return getDummyFilesForCS3Share(this._state);
    }

    createCheckpoint(localPath: string): Promise<Contents.ICheckpointModel> {
        return getDummyFilesForCS3Share(this._state);
    }

    listCheckpoints(localPath: string): Promise<Contents.ICheckpointModel[]> {
        return getDummyFilesForCS3Share(this._state);
    }

    restoreCheckpoint(localPath: string, checkpointID: string): Promise<void> {
        return getDummyFilesForCS3Share(this._state);
    }

    deleteCheckpoint(localPath: string, checkpointID: string): Promise<void> {
        return getDummyFilesForCS3Share(this._state);
    }

}
