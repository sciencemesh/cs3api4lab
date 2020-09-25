import React from 'react';
import {Contents} from "@jupyterlab/services";
import moment from "moment";

type InfoProps = {
    content: Contents.IModel
}

const Info = (props :InfoProps) :JSX.Element => {
    return (
        <table className='jp-file-detail'>
            <tbody>
            { props.content.mimetype ?
                (
                    <tr>
                        <th>Mimetype:</th>
                        <td>{props.content.mimetype}</td>
                    </tr>
                ) : ''
            }
            { props.content.size ?
                (
                    <tr>
                        <th>Size:</th>
                        <td>{props.content.size} Bytes</td>
                    </tr>
                ) : ''
            }
            <tr>
                <th>Type:</th>
                <td>{props.content.type}</td>
            </tr>
            <tr>
                <th>Writable:</th>
                <td>{props.content.writable ? 'Yes' : 'No'}</td>
            </tr>
            <tr>
                <th>Created:</th>
                <td>{moment(Date.parse(props.content.created)).format('LLLL')}</td>
            </tr>
            <tr>
                <th>Last Modified:</th>
                <td>{moment(Date.parse(props.content.last_modified)).format('LLLL')}</td>
            </tr>
            </tbody>
        </table>
    );
}

export default Info;
