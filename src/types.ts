import { Contents } from '@jupyterlab/services';
import { IStateDB } from '@jupyterlab/statedb';
import { FileBrowser } from '@jupyterlab/filebrowser';

export type ShareFormProps = {
  getUsers: (query: string) => Promise<Array<UsersRequest>>;
  fileInfo: Contents.IModel;
  getGrantees: () => void;
};
export type CreateShareProps = {
  fileInfo: Contents.IModel;
  getGrantees: () => void;
};
export type MainProps = {
  fileInfo: Contents.IModel;
  tabname: string;
};
export type MenuProps = {
  tabHandler: (tabname: string) => void;
  tabname: string;
};
export type ContentProps = {
  content: Contents.IModel;
  contentType: string;
};
export type HeaderProps = {
  fileInfo: Contents.IModel;
};
export type ShareProps = {
  fileInfo: Contents.IModel;
};
export type InfoboxProps = {
  fileInfo: Contents.IModel;
  tabname: string;
};
export type InfoProps = {
  content: Contents.IModel;
};

export type BottomProps = {
  db: IStateDB;
  browser: FileBrowser;
};

export type UsersRequest = {
  display_name: string;
  idp: string;
  opaque_id: string;
  permissions: string;
  full_name: string;
};

export type User = {
  displayName: string;
  idp: string;
  opaqueId: string;
  permissions: string;
  fullName: string;
};

export type Grantee = {
  opaque_id: string;
  permissions: string;
  idp: string;
};

export type PendingSharesOptions = {
  id: string;
  title: {
    caption: string;
    label: string;
  };
};

export type PendingShareProp = {
  content: Contents.IModel & {
    owner: string;
    opaque_id: string;
  };
  acceptShare: (pendingShare: any) => Promise<void>;
  declineShare: (pendingShare: any) => Promise<void>;
};

export type AcceptButtonProps = {
  content: Contents.IModel & {
    owner: string;
  };
  acceptShare: (pendingShare: any) => Promise<void>;
};

export type DeclineButtonProps = {
  content: Contents.IModel & {
    owner: string;
  };
  declineShare: (pendingShare: any) => Promise<void>;
};

export type PendingSharesContentProps = {
  hideWidget: () => void;
  showWidget: () => void;
};
