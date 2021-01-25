import React, {useEffect, useState} from 'react';
import {Contents} from "@jupyterlab/services";
import {ReactWidget} from "@jupyterlab/apputils";
import {findFileIcon, requestAPI} from './services';
import moment from "moment";
import {ContentProps, HeaderProps, InfoProps, MainProps, MenuProps, ShareProps, SharesProps} from "./types";


/**
 * Main container.
 *
 * @constructor
 */
class Main extends React.Component<any, any> {
    public state = {
        activeTab: 'info',
        grantees: new Map()
    }

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
    }

    protected getGranteesForResource = async () => {
        let resource = '/home/' + this.props.fileInfo.path.replace('cs3drive:', '');

        const grantees = await requestAPI<any>('/api/cs3/shares/file?file_path=' + resource, {
            method: 'GET',
        });

        const granteesSet = new Map();
        grantees.shares.forEach((item: any) => {
            granteesSet.set(item.grantee.opaque_id, item.grantee.permissions);
        });

        this.setState({...this.state, grantees: granteesSet});
    }

    public componentDidMount() {
        this.getGranteesForResource();
    }

    public render() {
        return (
            <div className='jp-file-info'>
                <Header fileInfo={this.props.fileInfo}/>
                <Menu tabHandler={this.switchTabs}/>
                <Content
                    contentType={this.state.activeTab}
                    content={this.props.fileInfo}
                    grantees={this.state.grantees}
                />
            </div>
        );
    }
}

export const Menu = (props: MenuProps): JSX.Element => {
    const [activeTab, setActiveTab] = useState('info');

    return (<>
            <nav className='jp-file-info-menu'>
                <ul>
                    <li className={activeTab == 'info' ? 'active' : ''} onClick={() => {
                        setActiveTab('info');
                        props.tabHandler('info')
                    }}>INFO
                    </li>
                    <li className={activeTab == 'share' ? 'active' : ''} onClick={() => {
                        setActiveTab('share');
                        props.tabHandler('shares')
                    }}>SHARES
                    </li>
                    <li>LINKS</li>
                </ul>
            </nav>
            <hr className='jp-file-info-menu-separator'/>
        </>
    );
}


const Content = (props: ContentProps): JSX.Element => {
    let elementToDisplay: JSX.Element;

    switch (props.contentType) {
        case 'shares':
            elementToDisplay = Shares({grantees: props.grantees});
            break;

        case 'info':
        default:
            elementToDisplay = Info({content: props.content});
    }

    return (
        <div className='jp-file-info-content'>
            {elementToDisplay}
        </div>
    );
}


const Header = (props: HeaderProps): JSX.Element => {
    const Icon = findFileIcon(props.fileInfo);

    return (
        <div className='jp-file-info-header'>
            <Icon.react className='jp-file-info-header-icon'/>
            <div className='file-info-header-title'>
                {props.fileInfo.name}
            </div>
        </div>
    );
}


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
        return (
            <Main fileInfo={this.fileInfo}/>
        )
    }
}

// TABS

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

// type PublicLinksProps = {
//
// }
// const PublicLinks = (props :PublicLinksProps) :JSX.Element => {
//     return (<div>PUBLIC LINKS</div>);
// }


const Shares = (props :SharesProps) :JSX.Element => {
    const [grantees] = useState(props.grantees);
    const [granteesList, setGranteesList] = useState([]);

    const refresh = (grantees :Map<string,string>) :void => {
        const granteesListArr :Array<Object> = [];
        grantees.forEach(((permission, grantee) => {
            granteesListArr.push(<div className='jp-shares-element' key={grantee}>
                <div className='jp-shares-owner'>{grantee}</div>
                <div className='jp-shares-label'>
                    <span className={permission}>{permission}</span>
                </div>
            </div>);
        }));

        setGranteesList(granteesListArr);
    }

    useEffect(() => {
        refresh(grantees)
    }, [grantees]);

    const showedValues = (event :React.ChangeEvent<HTMLInputElement>) :void => {
        const granteesFiltered = new Map(grantees);
        granteesFiltered.forEach( (permission, grantee) => {
            if (grantee.toString().search(event.target.value.toString()) == -1) {
                granteesFiltered.delete(grantee);
            }
        });

        refresh(granteesFiltered);
    };

    return (
        <div className='jp-shares'>
            <div className='jp-shares-search-container'>
                <input type='text' className='jp-shares-search' onChange={showedValues}/>
            </div>

            <div className='jp-shares-list-container'>
                {
                    granteesList.map((grantee) => {
                        return grantee;
                    })
                }
            </div>
        </div>
    );
}
