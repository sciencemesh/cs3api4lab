import React from 'react';
import Menu from '../components/Menu';
import Content from "../components/Content";
import Header from "../components/Header";
import {Contents} from "@jupyterlab/services";
import {requestAPI} from "../services/requestAPI";

type MainProps = {
    fileInfo: Contents.IModel
}

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
    protected switchTabs = (tabname :string) :void => {
        this.setState({
            activeTab: tabname
        });
    }

    protected getGranteesForResource = async () => {
        let resource = '/home/' + this.props.fileInfo.path.replace('cs3drive:', '');

        const grantees  =  await requestAPI<any>('/api/cs3/shares/file?file_path=' + resource, {
            method: 'GET',
        });

        const granteesSet = new Map();
        grantees.shares.forEach((item :any) => {
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

export default Main;
