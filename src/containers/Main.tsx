import React from 'react';
import Menu from '../components/Menu';
import Content from "../components/Content";
import Header from "../components/Header";
import {Contents} from "@jupyterlab/services";

// Services
// import {requestAPI} from "../services/requestAPI";

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
        activeTab: 'info'
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

    public render() {
        return (
            <div className='jp-file-info'>
                <Header fileInfo={this.props.fileInfo}/>
                <Menu tabHandler={this.switchTabs}/>
                <Content contentType={this.state.activeTab} content={this.props.fileInfo} />
            </div>
        );
    }
}

export default Main;
