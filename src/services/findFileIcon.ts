import {Contents} from "@jupyterlab/services";
import {LabIcon} from "@jupyterlab/ui-components";
import {DocumentRegistry} from "@jupyterlab/docregistry";

export const findFileIcon = (fileInfo :Contents.IModel) :LabIcon => {
    let splitName = fileInfo.name.split('.');
    let fileExtention = '.' + splitName[splitName.length-1];

    let fileType = DocumentRegistry.defaultFileTypes
        .filter( (fileType: Partial<DocumentRegistry.IFileType>) => {
            return fileType.contentType == "directory" || fileType.extensions.lastIndexOf(fileExtention) >= 0;
        });

    return (fileType.length > 0 ) ? fileType[0].icon : LabIcon.resolve({
        icon: 'ui-components:file'
    });
}
