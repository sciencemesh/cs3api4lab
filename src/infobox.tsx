import React, {useEffect, useState} from 'react';
import {Contents} from '@jupyterlab/services';
import {ReactWidget} from '@jupyterlab/apputils';
import {findFileIcon, requestAPI} from './services';
import moment from 'moment';
import {
    ContentProps,
    HeaderProps,
    InfoProps,
    MainProps,
    MenuProps,
    ShareProps,
    SharesProps, User,
    UsersRequest
} from './types';
import {LabIcon} from "@jupyterlab/ui-components";

/**
 * Main container.
 *
 * @constructor
 */
class Main extends React.Component<any, any> {
    public state = {
        activeTab: 'info',
        grantees: new Map()
    };

    /**
     * Main component constructor.
     *
     * @param props
     */
    public constructor(props: MainProps) {
        super(props);
        this.setState({
            ...this.state,
            props
        });
    }

    /**
     * Switch between views on file properties.
     *
     * @param tabname
     */
    protected switchTabs = (tabname: string): void => {
        this.setState({
            activeTab: tabname
        });
    };

    // protected getGranteesForResource = async () :Promise<Map<string, string>> => {
    //
    //     // return grantees;
    // }

    public render() {
        return (
            <div className="jp-file-info">
                <Header fileInfo={this.props.fileInfo}/>
                <Menu tabHandler={this.switchTabs}/>
                <Content
                    contentType={this.state.activeTab}
                    content={this.props.fileInfo}
                    // getGrantees={this.getGranteesForResource}
                />
            </div>
        );
    }
}

export const Menu = (props: MenuProps): JSX.Element => {
    const [activeTab, setActiveTab] = useState('info');

    return (
        <>
            <nav className="jp-file-info-menu">
                <ul>
                    <li
                        className={activeTab == 'info' ? 'active' : ''}
                        onClick={() => {
                            setActiveTab('info');
                            props.tabHandler('info');
                        }}
                    >
                        INFO
                    </li>
                    <li
                        className={activeTab == 'share' ? 'active' : ''}
                        onClick={() => {
                            setActiveTab('share');
                            props.tabHandler('shares');
                        }}
                    >
                        SHARES
                    </li>
                    <li>LINKS</li>
                </ul>
            </nav>
            <hr className="jp-file-info-menu-separator"/>
        </>
    );
};

const Content = (props: ContentProps): JSX.Element => {
    let elementToDisplay: JSX.Element;

    switch (props.contentType) {
        case 'shares':
            elementToDisplay = Shares({content: props.content});
            break;

        case 'info':
        default:
            elementToDisplay = Info({content: props.content});
    }

    return <div className="jp-file-info-content">{elementToDisplay}</div>;
};

const Header = (props: HeaderProps): JSX.Element => {
    const Icon :LabIcon = findFileIcon(props.fileInfo);

    return (
        <div className="jp-file-info-header">
            <Icon.react className="jp-file-info-header-icon"/>
            <div className="file-info-header-title">{props.fileInfo.name}</div>
        </div>
    );
};

/**
 * InfoboxWidget container.
 */
export class InfoboxWidget extends ReactWidget {
    private readonly fileInfo: Contents.IModel;

    public constructor(props: ShareProps) {
        super();
        this.addClass('jp-ReactWidget');
        this.fileInfo = props.fileInfo;
    }

    protected render(): JSX.Element {
        return <Main fileInfo={this.fileInfo}/>;
    }
}

// TABS

const Info = (props: InfoProps): JSX.Element => {
    return (
        <table className="jp-file-detail">
            <tbody>
            {props.content.mimetype ? (
                <tr>
                    <th>Mimetype:</th>
                    <td>{props.content.mimetype}</td>
                </tr>
            ) : (
                ''
            )}
            {props.content.size ? (
                <tr>
                    <th>Size:</th>
                    <td>{props.content.size} Bytes</td>
                </tr>
            ) : (
                ''
            )}
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
                <td>
                    {moment(Date.parse(props.content.last_modified)).format('LLLL')}
                </td>
            </tr>
            </tbody>
        </table>
    );
};

// type PublicLinksProps = {
//
// }
// const PublicLinks = (props :PublicLinksProps) :JSX.Element => {
//     return (<div>PUBLIC LINKS</div>);
// }

const Shares = (props: SharesProps): JSX.Element => {
    const [grantees, setGrantees] = useState([{
        displayName: '',
        name: '',
        idp: '',
        opaqueId: '',
        permission: ''
    }]);
    const [filteredGrantees, setFilteredGrantees] = useState([{
        displayName: '',
        name: '',
        idp: '',
        opaqueId: '',
        permission: ''
    }]);

    useEffect(() => {
        const getGrantees = async (): Promise<any> => {
            const resource = '/' + props.content.path.replace('cs3driveShareByMe:', '');

            requestAPI<any>('/api/cs3/shares/file?file_path=' + resource, {
                method: 'GET'
            }).then(async granteesRequest => {
                if (!granteesRequest.shares) {
                    return false;
                }

                const granteesSet: Array<{
                    opaque_id: string;
                    permission: string;
                    idp: string;
                }> = [];
                granteesRequest.shares.forEach((item: any) => {
                    granteesSet.push({
                        opaque_id: item.grantee.opaque_id,
                        permission: item.grantee.permissions,
                        idp: item.grantee.idp
                    });
                });

                if (granteesSet.length <= 0) {
                    return false;
                }

                const granteesPromises: Array<any> = [];
                for (const gr of granteesSet) {
                    granteesPromises.push(await getUsernames(gr.opaque_id, gr.idp));
                }

                Promise.all([...granteesPromises]).then(responses => {
                    const granteesArray :[User] = [{
                        displayName: '',
                        name: '',
                        idp: '',
                        opaqueId: '',
                        permission: ''
                    }];
                    for (const res of responses) {
                        for (const gr of granteesSet) {
                            if (gr.opaque_id == res.opaque_id) {
                                granteesArray.push({
                                    idp: res.idp,
                                    opaqueId: res.opaque_id,
                                    name: res.name,
                                    displayName: res.display_name,
                                    permission: res.permission
                                });
                            }
                        }
                    }

                    setGrantees(granteesArray);
                    setFilteredGrantees(granteesArray);
                });
            });

            return new Promise(resolve => {
                resolve(null);
            });
        };

        getGrantees();
    }, []);

    const getUsernames = async (
        opaqueId: string,
        idp: string
    ): Promise<UsersRequest> => {
        return await requestAPI<any>(
            '/api/cs3/user?opaque_id=' + opaqueId + '&idp=' + idp,
            {
                method: 'GET'
            }
        );
    };
    const filterGrantees = (
        event: React.ChangeEvent<HTMLInputElement>
    ): void => {
        setFilteredGrantees(
            grantees.filter(item => {
                if (event?.target.value.toString().trim() === '') {
                    return true;
                }

                return (
                    item.displayName
                        .toString()
                        .trim()
                        .search(new RegExp(event.target.value.toString().trim(), 'i')) != -1
                );
            })
        );
    };

    return (
        <div className="jp-shares">
            <div className="jp-shares-search-container">
                <input
                    type="text"
                    className="jp-shares-search"
                    onChange={filterGrantees}
                />
            </div>

            <div className="jp-shares-list-container">
                {filteredGrantees.map((granteeItem, key) => {
                    if (!granteeItem) {
                        return false;
                    }

                    return (
                        <div className="jp-shares-element" key={key}>
                            <div className="jp-shares-owner">{granteeItem.displayName}</div>
                            <div className="jp-shares-label">
                <span className={granteeItem.permission}>
                  {granteeItem.permission}
                </span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
