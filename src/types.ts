import {Contents} from "@jupyterlab/services";

export type ResultProps = {
    message: string;
}
export type ShareFormProps = {
    makeRequest: (params: object) => void;
    fileInfo: Contents.IModel;
}
export type CreateShareProps = {
    fileInfo: Contents.IModel;
}
export type WidgetProps = {
    fileInfo: Contents.IModel
}
export type MainProps = {
    fileInfo: Contents.IModel
}
export type MenuProps = {
    tabHandler: (tabname: string) => void
}
export type ContentProps = {
    content: Contents.IModel,
    contentType: string,
    grantees: Map<string, string>
}
export type HeaderProps = {
    fileInfo: Contents.IModel
}
export type ShareProps = {
    fileInfo: Contents.IModel,
}
export type InfoProps = {
    content: Contents.IModel
}
export type SharesProps = {
    grantees: Map<string, string>
}
