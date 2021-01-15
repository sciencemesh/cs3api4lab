import {Contents} from "@jupyterlab/services";
import {LabIcon} from "@jupyterlab/ui-components";
import {DocumentRegistry} from "@jupyterlab/docregistry";
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

export const findFileIcon = (fileInfo :Contents.IModel) :LabIcon => {
    let splitName = fileInfo.name.split('.');
    let fileExtension = '.' + splitName[splitName.length-1];

    let fileType = DocumentRegistry.defaultFileTypes
        .filter( (fileType: Partial<DocumentRegistry.IFileType>) => {
            return fileType.contentType == "directory" || fileType.extensions.lastIndexOf(fileExtension) >= 0;
        });

    return (fileType.length > 0 ) ? fileType[0].icon : LabIcon.resolve({
        icon: 'ui-components:file'
    });
}

/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
export async function requestAPI<T>(
    endPoint = '',
    init: RequestInit = {}
): Promise<T> {
    // Make request to Jupyter API
    const settings = ServerConnection.makeSettings();
    const requestUrl = URLExt.join(
        settings.baseUrl,
        '',
        endPoint
    );

    let response: Response;
    try {
        response = await ServerConnection.makeRequest(requestUrl, init, settings);
    } catch (error) {
        throw new ServerConnection.NetworkError(error);
    }

    const data = await response.json();

    if (!response.ok) {
        throw new ServerConnection.ResponseError(response, data.message);
    }

    return data;
}
