import { Contents, ServerConnection } from '@jupyterlab/services';
import { DocumentRegistry } from '@jupyterlab/docregistry';
// import { ISignal } from '@lumino/signaling';
import {CS3ContainerFiles} from './CS3Drive';
import { Signal, ISignal } from '@lumino/signaling';
import {IStateDB} from '@jupyterlab/statedb';
import {IDocumentManager} from "@jupyterlab/docmanager";

// import {ICheckpointModel, ICreateOptions, IModel} from "@jupyterlab/services/lib/contents";

export class CS3Contents implements Contents.IDrive {
    private _docRegistry: DocumentRegistry;
    private _fileTypeForPath: (path: string) => DocumentRegistry.IFileType;
    private _fileTypeForContentsModel: (model: Partial<Contents.IModel>) => DocumentRegistry.IFileType;
    private _fileChanged = new Signal<this, Contents.IChangedArgs>(this);
    private _isDisposed = false;
    private _state :IStateDB;
    private _docManager :IDocumentManager;

    constructor(registry: DocumentRegistry, stateDB: IStateDB, docManager :IDocumentManager) {
        this._docRegistry = registry;
        this._docManager = docManager;

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
    get name(): 'CS3Drive' {
        return 'CS3Drive';
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
        return await CS3ContainerFiles(this._state, path);
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
        return this._docManager.services.contents.getDownloadUrl(localPath);
    };

    newUntitled(options?: Contents.ICreateOptions): Promise<Contents.IModel> {
        return this._docManager.services.contents.newUntitled(options);
    }

    delete(localPath: string): Promise<void> {
        return this._docManager.services.contents.delete(localPath);
    };

    rename(oldLocalPath: string, newLocalPath: string): Promise<Contents.IModel> {
        return this._docManager.services.contents.rename(oldLocalPath, newLocalPath);
    }

    save(localPath: string, options?: Partial<Contents.IModel>): Promise<Contents.IModel> {
        return this._docManager.services.contents.save(localPath, options);
    }

    copy(localPath: string, toLocalDir: string): Promise<Contents.IModel> {
        return this._docManager.services.contents.copy(localPath, toLocalDir);
    }

    createCheckpoint(localPath: string): Promise<Contents.ICheckpointModel> {
        return this._docManager.services.contents.createCheckpoint(localPath);
    }

    listCheckpoints(localPath: string): Promise<Contents.ICheckpointModel[]> {
        return this._docManager.services.contents.listCheckpoints(localPath);
    }

    restoreCheckpoint(localPath: string, checkpointID: string): Promise<void> {
        return this._docManager.services.contents.restoreCheckpoint(localPath, checkpointID);
    }

    deleteCheckpoint(localPath: string, checkpointID: string): Promise<void> {
        return this._docManager.services.contents.deleteCheckpoint(localPath, checkpointID);
    }
}
