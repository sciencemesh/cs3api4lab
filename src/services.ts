import { Contents } from '@jupyterlab/services';
import { LabIcon } from '@jupyterlab/ui-components';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { URLExt } from '@jupyterlab/coreutils';
import { ServerConnection } from '@jupyterlab/services';

export const findFileIcon = (fileInfo: Contents.IModel): LabIcon => {
  const splitName = fileInfo.name.split('.');
  const fileExtension = '.' + splitName[splitName.length - 1];

  const fileType: Partial<
    DocumentRegistry.IFileType
  >[] = DocumentRegistry.getDefaultFileTypes().filter(
    (fileType: Partial<DocumentRegistry.IFileType>) => {
      const fileTypeLastIndex:
        | number
        | undefined = fileType.extensions?.lastIndexOf(fileExtension);

      return (
        fileType.contentType === 'directory' ||
        (fileTypeLastIndex !== undefined && fileTypeLastIndex >= 0)
      );
    }
  );

  return fileType.length > 0
    ? (fileType[0].icon as LabIcon)
    : LabIcon.resolve({
        icon: 'ui-components:file'
      });
};

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
  const requestUrl = URLExt.join(settings.baseUrl, '', endPoint);

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    // console logging for troubleshooting
    console.error(JSON.stringify(error));
    throw new ServerConnection.NetworkError(error);
  }

  if (response.status === 204) {
    return Promise.resolve({} as T);
  }

  const data = await response.json();

  if (!response.ok) {
    if (data['error_message']) {
      // console logging for troubleshooting
      console.error(JSON.stringify(data['error_message']));
    }
    throw new ServerConnection.ResponseError(response, data.message);
  }

  return data;
}

/**
 * Format bytes to human readable string.
 */
export function formatFileSize(
  bytes: number,
  decimalPoint: number,
  k: number
): string {
  // https://www.codexworld.com/how-to/convert-file-size-bytes-kb-mb-gb-javascript/
  if (bytes === 0) {
    return '0 Bytes';
  }
  const dm = decimalPoint || 2;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  if (i >= 0 && i < sizes.length) {
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  } else {
    return String(bytes);
  }
}
