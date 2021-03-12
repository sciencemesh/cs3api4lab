import {Contents} from '@jupyterlab/services';

export type ResultProps = {
    message: string;
};
export type ShareFormProps = {
    makeRequest: (params: object) => void;
    getUsers: (query: string) => Promise<Array<UsersRequest>>;
    fileInfo: Contents.IModel;
};
export type CreateShareProps = {
    fileInfo: Contents.IModel;
};
export type WidgetProps = {
    fileInfo: Contents.IModel;
};
export type MainProps = {
    fileInfo: Contents.IModel;
};
export type MenuProps = {
    tabHandler: (tabname: string) => void;
};
export type ContentProps = {
    content: Contents.IModel;
    contentType: string;
    // getGrantees: Promise<Map<string, string>>
    // grantees: Map<string, string>
};
export type HeaderProps = {
    fileInfo: Contents.IModel;
};
export type ShareProps = {
    fileInfo: Contents.IModel;
};
export type InfoProps = {
    content: Contents.IModel;
};
export type SharesProps = {
    // grantees: Map<string, string>,
    content: Contents.IModel;
};

export type UsersRequest = {
    display_name: string;
    name: string;
    idp: string;
    opaque_id: string;
};

export type User = {
    displayName: string;
    name: string;
    idp: string;
    opaqueId: string;
};
