import React, { useState } from 'react';
import { Contents } from '@jupyterlab/services';
import { ReactWidget, WidgetTracker } from '@jupyterlab/apputils';
import { findFileIcon, requestAPI } from './services';
import { INotification } from 'jupyterlab_toastify';
import moment from 'moment';
import {
  ContentProps,
  CreateShareProps,
  HeaderProps,
  InfoProps,
  MainProps,
  MenuProps,
  ShareFormProps,
  ShareProps,
  UsersRequest
} from './types';
import { LabIcon } from '@jupyterlab/ui-components';
import Select, { SelectRenderer } from 'react-dropdown-select';

/**
 * Main container.
 *
 * @class
 */
class Main extends React.Component<any, any> {
  private readonly widgetTracker: WidgetTracker;
  public state = {
    activeTab: 'info',
    grantees: new Map()
  };

  /**
   * Main component constructor.
   *
   * @param props MainProps
   */
  public constructor(props: MainProps) {
    super(props);
    this.widgetTracker = props.widgetTracker;
  }

  /**
   * Switch between views on file properties.
   *
   * @param tabname string Active tab name
   */
  protected switchTabs = (tabname: string): void => {
    this.setState({
      activeTab: tabname
    });
  };

  public render(): JSX.Element {
    return (
      <div className="jp-file-info">
        <Header fileInfo={this.props.fileInfo} />
        <Menu tabHandler={this.switchTabs} />
        <Content
          contentType={this.state.activeTab}
          content={this.props.fileInfo}
          widgetTracker={this.widgetTracker}
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
            className={activeTab === 'info' ? 'active' : ''}
            onClick={(): void => {
              setActiveTab('info');
              props.tabHandler('info');
            }}
          >
            INFO
          </li>
          <li
            className={activeTab === 'share' ? 'active' : ''}
            onClick={(): void => {
              setActiveTab('share');
              props.tabHandler('shares');
            }}
          >
            SHARES
          </li>

          <li
            className={activeTab === 'sharefile' ? 'active' : ''}
            onClick={(): void => {
              setActiveTab('sharefile');
              props.tabHandler('sharefile');
            }}
          >
            SHARE FILE
          </li>
          <li>LINKS</li>
        </ul>
      </nav>
      <hr className="jp-file-info-menu-separator" />
    </>
  );
};

const Content = (props: ContentProps): JSX.Element => {
  let elementToDisplay: JSX.Element;

  switch (props.contentType) {
    case 'shares':
      elementToDisplay = Shares();
      break;
    case 'sharefile':
      elementToDisplay = CreateShare({
        fileInfo: props.content,
        widgetTracker: props.widgetTracker
      });
      break;
    case 'info':
    default:
      elementToDisplay = Info({ content: props.content });
  }

  return <div className="jp-file-info-content">{elementToDisplay}</div>;
};

const Header = (props: HeaderProps): JSX.Element => {
  const Icon: LabIcon = findFileIcon(props.fileInfo);

  return (
    <div className="jp-file-info-header">
      <Icon.react className="jp-file-info-header-icon" />
      <div className="file-info-header-title">{props.fileInfo.name}</div>
    </div>
  );
};

/**
 * InfoboxWidget container.
 */
export class InfoboxWidget extends ReactWidget {
  private readonly fileInfo: Contents.IModel;
  private readonly widgetTracker: WidgetTracker;

  public constructor(props: ShareProps) {
    super();
    this.addClass('jp-ReactWidget');
    this.fileInfo = props.fileInfo;
    this.widgetTracker = props.widgetTracker;
  }

  protected render(): JSX.Element {
    return <Main fileInfo={this.fileInfo} widgetTracker={this.widgetTracker} />;
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
        ) : null}
        {props.content.size ? (
          <tr>
            <th>Size:</th>
            <td>{props.content.size} Bytes</td>
          </tr>
        ) : null}
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

const Shares = (): JSX.Element => {
  const [grantees] = useState([
    {
      displayName: '',
      name: '',
      idp: '',
      opaqueId: '',
      permission: ''
    }
  ]);
  const [filteredGrantees, setFilteredGrantees] = useState([
    {
      displayName: '',
      name: '',
      idp: '',
      opaqueId: '',
      permission: ''
    }
  ]);

  const filterGrantees = (event: React.ChangeEvent<HTMLInputElement>): void => {
    setFilteredGrantees(
      grantees.filter(item => {
        if (event?.target.value.toString().trim() === '') {
          return true;
        }

        return (
          item.displayName
            .toString()
            .trim()
            .search(new RegExp(event.target.value.toString().trim(), 'i')) !==
          -1
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

// SHARE A FILE

/**
 * Share form widget.
 *
 * @param shareProps ShareFormProps
 *
 * @returns JSX.Element
 */
const ShareForm: React.FC<ShareFormProps> = (
  shareProps: ShareFormProps
): JSX.Element => {
  const [userList, setUserList] = useState([]);
  const [selectedUser, setSelectedUser] = useState([
    {
      idp: '',
      grantee: ''
    }
  ]);

  const [formValues, setFormState] = useState({
    endpoint: '/',
    file_path: '/home/' + shareProps.fileInfo.path.replace('cs3drive:', ''),
    grantee: '',
    idp: '',
    role: 'viewer',
    grantee_type: 'user'
  });

  const getUsers = ({
    state
  }: SelectRenderer<Record<string, any>>): Array<string> => {
    if (state.search.length <= 0) {
      return [];
    }

    shareProps.getUsers(state.search).then(users => {
      const parsedUsers: any = [];

      let i = 1;
      for (const user of users) {
        parsedUsers.push({
          id: i++,
          name: user.display_name,
          displayName: user.display_name,
          idp: user.idp,
          grantee: user.opaque_id
        });
      }
      setUserList(parsedUsers);
    });

    return [];
  };

  const setFormStateFromValues = (
    param:
      | React.ChangeEvent<HTMLInputElement>
      | React.ChangeEvent<HTMLSelectElement>
  ): void => {
    const tmpFormState: any = { ...formValues };
    tmpFormState[param.target.name] = param.target.value;
    setFormState(tmpFormState);
  };

  const localMakeRequest = (): void => {
    const [user] = [...selectedUser];
    const _formValues = { ...formValues };

    _formValues.idp = user.idp;
    _formValues.grantee = user.grantee;

    shareProps.makeRequest(_formValues);
  };

  return (
    <div className="jp-shareform">
      <div className="jp-shareform-line">
        <div className="jp-shareform-title">Grantee</div>
        <div className="jp-shareform-element">
          <Select
            searchable={true}
            options={userList}
            values={[]}
            create={false}
            valueField="name"
            labelField="displayName"
            placeholder="Select user..."
            onChange={(userValue: any): void => {
              const user = userValue[0] as { [key: string]: string };
              setSelectedUser([
                {
                  idp: user['idp'],
                  grantee: user['grantee']
                }
              ]);
            }}
            handleKeyDownFn={getUsers}
          />
        </div>
      </div>
      <div className="jp-shareform-line">
        <div className="jp-shareform-title">Role</div>
        <div className="jp-shareform-title">
          <select onChange={setFormStateFromValues} name="role">
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
          </select>
        </div>
      </div>

      <button onClick={localMakeRequest}>Make request</button>
    </div>
  );
};

/**
 * Main container.
 *
 * @param props CreateShareProps
 *
 * @returns JSX.Element
 */
const CreateShare = (props: CreateShareProps): JSX.Element => {
  return (
    <>
      <ShareForm
        fileInfo={props.fileInfo}
        getUsers={async (query): Promise<Array<UsersRequest>> => {
          return await requestAPI('api/cs3/user/query?query=' + query, {});
        }}
        makeRequest={async (params: object): Promise<void> => {
          try {
            await requestAPI<any>('/api/cs3/shares', {
              method: 'POST',
              body: JSON.stringify(params)
            });

            await INotification.success('This file is now shared');
          } catch (e) {
            await INotification.error('Error encountered while sharing a file');
          }

          props.widgetTracker.currentWidget?.close();
        }}
      />
    </>
  );
};
