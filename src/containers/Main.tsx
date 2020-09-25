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
        grantees: {}
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
        let resource = '/home/' + this.props.fileInfo.path;

        const grantees  =  await requestAPI<any>('/api/cs3test/shares/file?file_id=' + resource, {
            method: 'GET',
        });

        this.setState({...this.state, grantees: grantees});
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
