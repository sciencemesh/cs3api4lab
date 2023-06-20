import { Dialog, ReactWidget, showDialog } from '@jupyterlab/apputils';
import * as React from 'react';
import { ShareByMeProp, SharedByMeContentProps } from './types';
import { findFileIcon, requestAPI } from './services';
import { useEffect, useState } from 'react';
import { Time } from '@jupyterlab/coreutils';
import { Widget } from '@lumino/widgets';
import { FileBrowserModel } from '@jupyterlab/filebrowser';
import { Cs3Panel } from './cs3panel';
import { shareIcon } from './icons';
import { InfoboxWidget } from './infobox';

export class SharedByMeListWrapper extends ReactWidget {
  private model: FileBrowserModel;
  private panel: Cs3Panel;
  constructor(model: FileBrowserModel, panel: Cs3Panel) {
    super();
    this.hide = this.hide.bind(this);
    this.show = this.show.bind(this);
    this.model = model;
    this.panel = panel;

    this.addClass('jp-pending-shares-listing-wrapper');
  }

  protected onResize(msg: Widget.ResizeMessage): void {
    const { width } =
      msg.width === -1 ? this.node.getBoundingClientRect() : msg;

    this.toggleClass('jp-pending-shares-narrow', width < 290);
  }

  protected render(): JSX.Element {
    return (
      <div className="jp-ShareListing-content">
        <SharedByMeContent
          hideWidget={this.hide}
          showWidget={this.show}
          model={this.model}
          panel={this.panel}
        />
      </div>
    );
  }
}

const SharedByMeContent = (props: SharedByMeContentProps): JSX.Element => {
  const [shareList, setShareList] = useState([]);

  const refreshPendingShares = async (): Promise<void> => {
    requestAPI('/api/cs3/shares/list', {
      method: 'GET'
    }).then((pendingRequest: any) => {
      setShareList(pendingRequest.content);
    });
  };

  useEffect((): void => {
    void refreshPendingShares();
  }, []);

  useEffect((): void => {
    if (shareList.length > 0) {
      props.showWidget();
    }
  }, [shareList]);

  return (
    <>
      <div className="jp-pending-shares-header">
        <div className="jp-pending-shares-header-item jp-pending-shares-header-item-name jp-share-button">
          <span>Name</span>
        </div>
        <div className="jp-pending-shares-narrow-column">...</div>
        <div className="jp-pending-shares-header-item jp-pending-shares-header-item-shared-by jp-pending-shares-header-item-shared-by-hidden">
          <span>Last Modified</span>
        </div>
        <div className="jp-pending-shares-header-item-buttons jp-pending-shares-header-item-shared-by-hidden" />
      </div>
      <ul className="jp-pending-shares-listing">
        {shareList.map((pendingShare: any) => {
          return (
            <SharedByMeElement
              content={pendingShare}
              model={props.model}
              panel={props.panel}
              key={pendingShare.opaque_id}
            />
          );
        })}
      </ul>
    </>
  );
};

const SharedByMeElement = (props: ShareByMeProp): JSX.Element => {
  const Icon = findFileIcon(props.content);
  const created = Time.format(
    new Date(props.content.created),
    'YYYY-MM-DD HH:mm:ss'
  );
  const lastModified = Time.format(
    new Date(props.content.last_modified),
    'YYYY-MM-DD HH:mm:ss'
  );

  const lastModifiedHuman = Time.formatHuman(
    new Date(props.content.last_modified)
  );
  const title = `Name: ${props.content.name}
Path: ${props.content.path}
Created: ${created}
Modified: ${lastModified}
Writable: ${props.content.writable}
  `;

  return (
    <li
      className="jp-pending-shares-listing-item"
      title={title}
      onDoubleClick={() => {
        if (props.content.type === 'directory') {
          props.panel.activateFileBrowserTab();
          void props.model.cd(props.content.path);
        }

        if (props.content.type !== 'directory') {
          props.model.manager.openOrReveal(props.content.path);
        }
      }}
    >
      <Icon.react className="jp-pending-shares-listing-icon" />
      <span className="jp-pending-shares-listing-name jp-share-name">
        {props.content.name}
      </span>
      <div className="jp-pending-shares-listing-narrow-column" />
      <span className="jp-pending-shares-listing-shared-by jp-pending-shares-listing-shared-by-hidden">
        {lastModifiedHuman}
      </span>
      <div className="jp-pending-shares-listing-buttons jp-share-button">
        <a
          onClick={() => {
            void showDialog({
              body: new InfoboxWidget({
                fileInfo: props.content,
                tabname: 'shares',
                type: 'share'
              }),
              buttons: [Dialog.okButton({ label: 'Close' })]
            });
          }}
        >
          <shareIcon.react width="16px" height="16px" />
        </a>
      </div>
    </li>
  );
};
