import { requestAPI } from './services';
import { ReadonlyJSONObject } from '@lumino/coreutils';
import { Contents, ServerConnection } from '@jupyterlab/services';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { ISignal, Signal } from '@lumino/signaling';
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
  readonly serverSettings: ServerConnection.ISettings;

  constructor(
    registry: DocumentRegistry,
    stateDB: IStateDB,
    docManager: IDocumentManager,
    serverSettings: ServerConnection.ISettings
  ) {
    this._docRegistry = registry;
    this._docManager = docManager;
    this.serverSettings = serverSettings;

    // Construct a function to make a best-guess IFileType
    // for a given path.
    this._fileTypeForPath = (path: string): DocumentRegistry.IFileType => {
      const fileTypes = registry.getFileTypesForPath(path);
      const fileType:
        | DocumentRegistry.IFileType
        | undefined = registry.getFileType('text');

      return fileTypes.length === 0 && fileType !== undefined
        ? fileType
        : fileTypes[0];
    };
    // Construct a function to return a best-guess IFileType
    // for a given contents model.
    this._fileTypeForContentsModel = (
      model: Partial<Contents.IModel>
    ): DocumentRegistry.IFileType => {
      return registry.getFileTypeForModel(model);
    };

    this._state = stateDB;
  }

  /**
   * The name of the drive.
   */
  get name(): string {
    return '';
  }

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
    const activeTab: string = (await this._state.fetch('activeTab')) as string;
    if (activeTab === 'cs3filebrowser' || activeTab === undefined) {
      return await CS3ContainerFiles('filelist', this._state, path, options);
    } else {
      return Promise.resolve({} as Contents.IModel);
    }
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

  /**
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

  newUntitled(
    options: Contents.ICreateOptions | undefined
  ): Promise<Contents.IModel> {
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
    const activeTab: string = (await this._state.fetch('activeTab')) as string;
    if (activeTab === 'sharesPanel') {
      return await CS3ContainerFiles('by_me', this._state, path, options);
    } else {
      return Promise.resolve({} as Contents.IModel);
    }
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
    const activeTab: string = (await this._state.fetch('activeTab')) as string;
    if (activeTab === 'sharesPanel') {
      return await CS3ContainerFiles('with_me', this._state, path, options);
    } else {
      return Promise.resolve({} as Contents.IModel);
    }
  }
}

export async function CS3ContainerFiles(
  readType: string,
  stateDB: IStateDB,
  path: string | null = null,
  options: Contents.IFetchOptions = {}
): Promise<any> {
  const share = await stateDB.fetch('share');
  const showHidden: boolean = (await stateDB.fetch('showHidden')) as boolean;
  let shareType;
  if (readType !== 'filelist') {
    shareType = readType;
  } else if (share !== undefined) {
    shareType = (share as ReadonlyJSONObject)['shareType'];
  }

  if (path !== '') {
    return await getFileList(path, options, showHidden, stateDB);
  }

  switch (shareType) {
    case 'by_me':
      return await getSharedByMe();
    case 'with_me':
      return await getSharedWithMe();
    case 'filelist':
    default:
      return await getFileList(path, options, showHidden, stateDB);
  }
}

async function getFileList(
  path: string | null,
  options: Contents.IFetchOptions,
  showHidden: boolean,
  stateDB: IStateDB
): Promise<any> {
  const { type, format, content } = options;

  let url = '';
  url += '?content=' + (content ? 1 : 0);
  if (type) {
    url += '&type=' + type;
  }
  if (format && type !== 'notebook') {
    url += '&format=' + format;
  }
  const result: Contents.IModel = await requestAPI(
    '/api/contents/' + path + '' + url,
    { method: 'get' }
  );

  // if it is a directory, count hidden files inside
  if (Array.isArray(result.content) && result.type === 'directory') {
    const hiddenFilesNo: number = result.content.filter(
      (file: { name: string }) => file.name.startsWith('.')
    ).length;
    await stateDB.save('hiddenFilesNo', hiddenFilesNo);

    if (!showHidden) {
      const filteredResult = JSON.parse(JSON.stringify(result));
      filteredResult.content = (result.content as Array<any>).filter(
        (file: { name: string }) => !file.name.startsWith('.')
      );
      return filteredResult;
    }
  }
  return result;
}

async function getSharedByMe(): Promise<any> {
  return await requestAPI('/api/cs3/shares/list?filter_duplicates=1', {
    method: 'get'
  });
}

async function getSharedWithMe(): Promise<any> {
  return await requestAPI('/api/cs3/shares/received', {
    method: 'get'
  });
}
