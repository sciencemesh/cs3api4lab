import React, { useEffect, useState, useCallback } from 'react';
import { Contents } from '@jupyterlab/services';
import { Dialog, ReactWidget } from '@jupyterlab/apputils';
import { formatFileSize, findFileIcon, requestAPI } from './services';
import { INotification } from 'jupyterlab_toastify';
import moment from 'moment';
import {
  ContentProps,
  Grantee,
  HeaderProps,
  InfoboxProps,
  InfoProps,
  MainProps,
  MenuProps,
  ShareFormProps,
  ShareProps,
  User,
  UsersRequest
} from './types';
import { LabIcon, closeIcon } from '@jupyterlab/ui-components';
import Select from 'react-dropdown-select';
import { debounce } from 'ts-debounce';

/**
 * Main container.
 *
 * @constructor
 */
class Main extends React.Component<any, any> {
  private readonly tabname: string;

  public state = {
    activeTab: 'info'
  };

  /**
   * Main component constructor.
   *
   * @param props
   */
  public constructor(props: MainProps) {
    super(props);
    this.tabname = props.tabname;
  }

  public componentDidMount() {
    this.setState({
      activeTab: this.tabname
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

  public render() {
    return (
      <div className="jp-file-info">
        <Header fileInfo={this.props.fileInfo} />
        <Menu tabHandler={this.switchTabs} tabname={this.tabname} />
        <Content
          contentType={this.state.activeTab}
          content={this.props.fileInfo}
        />
      </div>
    );
  }
}

export const Menu = (props: MenuProps): JSX.Element => {
  const [activeTab, setActiveTab] = useState(props.tabname);

  return (
    <>
      <nav className="jp-file-info-menu">
        <ul>
          <li
            className={activeTab === 'info' ? 'active' : ''}
            onClick={() => {
              setActiveTab('info');
              props.tabHandler('info');
            }}
          >
            INFO
          </li>
          <li
            className={activeTab === 'shares' ? 'active' : ''}
            onClick={() => {
              setActiveTab('shares');
              props.tabHandler('shares');
            }}
          >
            SHARES
          </li>
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
      elementToDisplay = Shares({
        fileInfo: props.content
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
  private readonly tabname: string;

  public constructor(props: InfoboxProps) {
    super();
    this.addClass('jp-ReactWidget');
    this.fileInfo = props.fileInfo;
    this.tabname = props.tabname;
  }

  protected render(): JSX.Element {
    return <Main fileInfo={this.fileInfo} tabname={this.tabname} />;
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
            <td>{formatFileSize(props.content.size, 1, 1024)}</td>
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

const Shares = (props: ShareProps): JSX.Element => {
  const [grantees, setGrantees] = useState<User[]>([]);
  const [share, setShare] = useState<any>({});

  const getGrantees = async (): Promise<any> => {
    requestAPI<any>(`/api/cs3/shares/file?file_path=${props.fileInfo.path}`, {
      method: 'GET'
    }).then(async granteesRequest => {
      if (granteesRequest.shares.length <= 0) {
        setGrantees([]);
        return false;
      }

      setShare(granteesRequest);
      const granteesSet: Array<Grantee> = [];
      granteesRequest.shares.forEach((item: any) => {
        granteesSet.push({
          opaque_id: item.grantee.opaque_id,
          permissions: item.grantee.permissions,
          idp: item.grantee.idp
        });
      });

      if (granteesSet.length <= 0) {
        return false;
      }

      const granteesPromises: Array<UsersRequest> = [];
      for (const gr of granteesSet) {
        granteesPromises.push(await getUsernames(gr.opaque_id, gr.idp));
      }

      Promise.all([...granteesPromises]).then(responses => {
        const granteesArray: User[] = [];

        for (const res of responses) {
          for (const gr of granteesSet) {
            if (gr.opaque_id === res.opaque_id) {
              granteesArray.push({
                idp: res.idp,
                opaqueId: res.opaque_id,
                fullName: res.full_name,
                displayName: res.display_name,
                permissions: gr.permissions
              });
            }
          }
        }

        setGrantees(granteesArray);
      });
    });

    return new Promise(resolve => {
      resolve(null);
    });
  };

  useEffect(() => {
    void getGrantees();
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

  return (
    <div className="jp-shares">
      <div>
        <ShareForm
          fileInfo={props.fileInfo}
          getUsers={async (query): Promise<Array<UsersRequest>> => {
            return await requestAPI('/api/cs3/user/query?query=' + query, {});
          }}
          getGrantees={getGrantees}
        />
      </div>

      <hr className="jp-file-info-menu-separator" />
      <div className="jp-shares-list-container">
        {grantees.map((granteeItem, key) => {
          if (!granteeItem) {
            return false;
          }

          return (
            <div className="jp-shares-element" key={key}>
              <div className="jp-shares-owner">{granteeItem.fullName}</div>
              <div className="jp-shares-label">
                <Select
                  values={[
                    {
                      name: granteeItem.permissions
                    }
                  ]}
                  searchable={false}
                  valueField="name"
                  labelField="name"
                  multi={false}
                  className="jp-share-permission"
                  options={[
                    {
                      name: 'viewer'
                    },
                    {
                      name: 'editor'
                    }
                  ]}
                  onChange={async selected => {
                    const selectedValue = selected[0].name;
                    const selectedShare = share.shares
                      .filter((item: any) => {
                        return item.grantee.opaque_id === granteeItem.opaqueId;
                      })
                      .pop();

                    await requestAPI('/api/cs3/shares', {
                      method: 'PUT',
                      body: JSON.stringify({
                        role: selectedValue,
                        share_id: selectedShare.opaque_id
                      })
                    });
                  }}
                />
              </div>
              <div>
                <button
                  style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    padding: '5px',
                    cursor: 'pointer'
                  }}
                  onClick={() => {
                    const selectedShare = share.shares
                      .filter((item: any) => {
                        return item.grantee.opaque_id === granteeItem.opaqueId;
                      })
                      .pop();
                    requestAPI(
                      `/api/cs3/shares?share_id=${selectedShare.opaque_id}`,
                      {
                        method: 'DELETE'
                      }
                    ).then(() => {
                      void getGrantees();
                    });
                  }}
                >
                  <closeIcon.react />
                </button>
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
 * @param shareProps
 *
 * @constructor
 */

const ShareForm: React.FC<ShareFormProps> = (
  shareProps: ShareFormProps
): JSX.Element => {
  const [searchString, setSearchString] = useState('');
  const [userList, setUserList] = useState([]);

  const getUsers = async (searchStr: string): Promise<void> => {
    if (searchStr.length <= 0) {
      return;
    }

    shareProps.getUsers(searchStr).then(users => {
      const parsedUsers: any = [];

      let i = 1;

      for (const user of users) {
        const itemExists: number = parsedUsers.filter((item: any) => {
          return item.grantee === user.opaque_id && item.idp === user.idp;
        }).length;

        if (itemExists <= 0) {
          parsedUsers.push({
            id: i++,
            name: user.display_name,
            displayName: user.display_name,
            idp: user.idp,
            grantee: user.opaque_id,
            fullName: user.full_name
          });
        }
      }
      setUserList(parsedUsers);
    });
  };

  const debounceHook = useCallback(
    debounce(searchStr => {
      void getUsers(searchStr);
    }, 500),
    []
  );

  useEffect(() => {
    void debounceHook(searchString);
    return;
  }, [searchString]);

  return (
    <div className="jp-shareform">
      <div className="jp-shareform-line">
        <div className="jp-shareform-element">
          <Select
            clearOnSelect={true}
            clearOnBlur={true}
            clearable={true}
            backspaceDelete={true}
            searchable={true}
            multi={false}
            options={userList}
            values={[]}
            create={false}
            valueField="name"
            labelField="fullName"
            placeholder="Select user..."
            onChange={async (userValue: any) => {
              if (userValue.length === 0) {
                return;
              }

              const user = userValue[0] as { [key: string]: string };
              const formValues = {
                endpoint: '/',
                file_path:
                  '/' + shareProps.fileInfo.path.replace('cs3drive:', ''),
                grantee: user.grantee,
                idp: user.idp,
                role: 'viewer',
                grantee_type: 'user'
              };

              try {
                await requestAPI<any>('/api/cs3/shares', {
                  method: 'POST',
                  body: JSON.stringify(formValues)
                });

                shareProps.getGrantees();
                await INotification.success('This file is now shared');
              } catch (e) {
                await INotification.error(
                  'Error encountered while sharing a file'
                );
              }
            }}
            searchFn={({ state, methods }): never[] => {
              setSearchString(state.search);
              return methods.sortBy().filter(item => {
                return true;
              });
            }}
          />
        </div>
      </div>
    </div>
  );
};

export function createInfobox(
  fileInfo: Contents.IModel,
  tabname: string
): Dialog<any> {
  return new Dialog({
    body: new InfoboxWidget({
      fileInfo: fileInfo,
      tabname: tabname
    }),
    buttons: [Dialog.okButton({ label: 'Close' })]
  });
}
