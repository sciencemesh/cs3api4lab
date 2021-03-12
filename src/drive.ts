import { requestAPI } from './services';
import { ReadonlyJSONObject } from '@lumino/coreutils';
import { Contents, ServerConnection } from '@jupyterlab/services';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { Signal, ISignal } from '@lumino/signaling';
import { IStateDB } from '@jupyterlab/statedb';
import { IDocumentManager } from '@jupyterlab/docmanager';

export class CS3Contents implements Contents.IDrive {
  protected _docRegistry: DocumentRegistry;
  protected _fileTypeForPath: (path: string) => DocumentRegistry.IFileType;
  protected _fileTypeForContentsModel: (
    model: Partial<Contents.IModel>
  ) => DocumentRegistry.IFileType;
  protected _fileChanged = new Signal<this, Contents.IChangedArgs>(this);
  protected _isDisposed = false;
  protected _state: IStateDB;
  protected _docManager: IDocumentManager;

  constructor(
    registry: DocumentRegistry,
    stateDB: IStateDB,
    docManager: IDocumentManager
  ) {
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

    console.log(
      'CS3Contents: ',
      this._docRegistry,
      this._fileTypeForPath,
      this._fileTypeForContentsModel
    );
  }

  refresh() {
    console.log('refresh');
  }

  /**
   * The name of the drive.
   */
  get name(): string {
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
    return await CS3ContainerFiles('filelist', this._state, path, options);
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
  }

  newUntitled(options?: Contents.ICreateOptions): Promise<Contents.IModel> {
    return this._docManager.services.contents.newUntitled(options);
  }

  delete(localPath: string): Promise<void> {
    return this._docManager.services.contents.delete(localPath);
  }

  rename(oldLocalPath: string, newLocalPath: string): Promise<Contents.IModel> {
    return this._docManager.services.contents.rename(
      oldLocalPath,
      newLocalPath
    );
  }

  save(
    localPath: string,
    options?: Partial<Contents.IModel>
  ): Promise<Contents.IModel> {
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
    return this._docManager.services.contents.restoreCheckpoint(
      localPath,
      checkpointID
    );
  }

  deleteCheckpoint(localPath: string, checkpointID: string): Promise<void> {
    return this._docManager.services.contents.deleteCheckpoint(
      localPath,
      checkpointID
    );
  }
}

export class CS3ContentsShareByMe extends CS3Contents {
  get name(): string {
    return 'cs3driveShareByMe';
  }

  async get(
    path: string,
    options?: Contents.IFetchOptions
  ): Promise<Contents.IModel> {
    return await CS3ContainerFiles('by_me', this._state, path, options);
  }
}

export class CS3ContentsShareWithMe extends CS3Contents {
  get name(): string {
    return 'cs3driveShareWithMe';
  }

  async get(
    path: string,
    options?: Contents.IFetchOptions
  ): Promise<Contents.IModel> {
    return await CS3ContainerFiles('with_me', this._state, path, options);
  }
}

export async function CS3ContainerFiles(
  readType: string,
  stateDB: IStateDB,
  path: string = null,
  options: Contents.IFetchOptions = null
): Promise<any> {
  const share = await stateDB.fetch('share');

  let shareType;
  if (readType != 'filelist') {
    shareType = readType;
  } else {
    shareType = (share as ReadonlyJSONObject)['share_type'];
  }

  if (path != '') {
    return await getFileList(path, options);
  }

  // switch (shareType) {
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

async function getFileList(
  path: string,
  options: Contents.IFetchOptions
): Promise<any> {
  const { type, format, content } = options;

  let url = '';
  url += '?content=' + (content ? 1 : 0);
  if (type) {
    url += '&type=' + type;
  }
  if (format && type != 'notebook') {
    url += '&format=' + format;
  }

  return await requestAPI('/api/contents/' + path + '' + url, {
    method: 'get'
  });
}

async function getSharedByMe(): Promise<any> {
  return await requestAPI('/api/cs3/shares/list', {
    method: 'get'
  });
}

async function getSharedWithMe(): Promise<any> {
  return await requestAPI('/api/cs3/shares/received', {
    method: 'get'
  });
}
