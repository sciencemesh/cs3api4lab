import { ReactWidget } from '@jupyterlab/apputils';
import { PanelLayout, Widget } from '@lumino/widgets';
import * as React from 'react';
import { acceptIcon, declineIcon } from './icons';
import {
  AcceptButtonProps,
  DeclineButtonProps,
  PendingShareProp,
  PendingSharesOptions
} from './types';
import { findFileIcon, requestAPI } from './services';
import { useEffect, useState } from 'react';
import { Time } from '@jupyterlab/coreutils';
import { Message } from '@lumino/messaging';

export class Cs3PendingSharesWidget extends Widget {
  layout: PanelLayout;
  private header: PendingSharesHeader;
  private content: PendingSharesListWrapper;

  constructor(options: PendingSharesOptions) {
    super();
    this.id = options.id;
    this.title.label = options.title.label;
    this.title.caption = options.title.caption;
    this.title.closable = false;

    this.layout = new PanelLayout();

    this.header = new PendingSharesHeader({
      title: {
        label: this.title.label
      }
    });

    this.content = new PendingSharesListWrapper();
  }

  protected onAfterShow(msg: Message): void {
    super.onAfterShow(msg);
    this.layout.addWidget(this.header);
    this.layout.addWidget(this.content);
  }

  protected onAfterHide(msg: Message): void {
    super.onAfterHide(msg);
    this.layout.removeWidget(this.header);
    this.layout.removeWidget(this.content);
  }

  protected onResize(msg: Widget.ResizeMessage): void {
    const { width } =
      msg.width === -1 ? this.node.getBoundingClientRect() : msg;

    this.toggleClass('jp-pending-shares-narrow', width < 290);
  }
}

class PendingSharesListWrapper extends ReactWidget {
  constructor() {
    super();
    this.addClass('jp-pending-shares-listing-wrapper');
  }

  protected render(): JSX.Element {
    return <PendingSharesContent />;
  }
}

const PendingSharesContent = (): JSX.Element => {
  const [pendingShares, setPendingShares] = useState([]);

  const refreshPendingShares = async (): Promise<void> => {
    requestAPI('/api/cs3/shares/received?status=pending', {
      method: 'GET'
    }).then((pendingRequest: any) => {
      setPendingShares(pendingRequest.content);
    });
  };

  const acceptShare = async (pendingShare: any): Promise<void> => {
    requestAPI('/api/cs3/shares/received', {
      method: 'PUT',
      body: JSON.stringify({
        share_id: pendingShare.opaque_id,
        state: 'accepted'
      })
    }).then(() => {
      refreshPendingShares();
    });
  };

  const declineShare = async (pendingShare: any): Promise<void> => {
    requestAPI('/api/cs3/shares/received', {
      method: 'PUT',
      body: JSON.stringify({
        share_id: pendingShare.opaque_id,
        state: 'rejected'
      })
    }).then(() => {
      refreshPendingShares();
    });
  };

  useEffect((): void => {
    void refreshPendingShares();
  }, []);

  return (
    <>
      <div className="jp-pending-shares-header">
        <div className="jp-pending-shares-header-item jp-pending-shares-header-item-name">
          <span>Name</span>
        </div>
        <div className="jp-pending-shares-narrow-column">...</div>
        <div className="jp-pending-shares-header-item jp-pending-shares-header-item-shared-by jp-pending-shares-header-item-shared-by-hidden">
          <span>Shared By</span>
        </div>
        <div className="jp-pending-shares-header-item-buttons" />
      </div>
      <ul className="jp-pending-shares-listing">
        {pendingShares.map((pendingShare: any) => {
          return (
            <PendingSharesElement
              content={pendingShare}
              acceptShare={acceptShare}
              declineShare={declineShare}
              key={pendingShare.opaque_id}
            />
          );
        })}
      </ul>
    </>
  );
};

class PendingSharesHeader extends ReactWidget {
  constructor(options: any) {
    super();
    this.addClass('jp-pending-shares-content');
    this.title.label = options.title.label;
  }
  protected render(): JSX.Element {
    return (
      <>
        <div className="jp-pending-shares-title c3-title-widget">
          {this.title.label}
        </div>
      </>
    );
  }
}

const PendingSharesElement = (props: PendingShareProp): JSX.Element => {
  const Icon = findFileIcon(props.content);
  const created = Time.format(
    new Date(props.content.created),
    'YYYY-MM-DD HH:mm:ss'
  );
  const lastModified = Time.format(
    new Date(props.content.last_modified),
    'YYYY-MM-DD HH:mm:ss'
  );

  const title = `Name: ${props.content.name}
Path: ${props.content.path}
Created: ${created}
Modified: ${lastModified}
Writable: ${props.content.writable}
  `;

  return (
    <li className="jp-pending-shares-listing-item" title={title}>
      <Icon.react className="jp-pending-shares-listing-icon" />
      <span className="jp-pending-shares-listing-name">
        <span>{props.content.name}</span>
      </span>
      <div className="jp-pending-shares-listing-narrow-column" />
      <span className="jp-pending-shares-listing-shared-by jp-pending-shares-listing-shared-by-hidden">
        {props.content.owner}
      </span>
      <div className="jp-pending-shares-listing-buttons">
        <AcceptButton content={props.content} acceptShare={props.acceptShare} />
        <RejectButton
          content={props.content}
          declineShare={props.declineShare}
        />
      </div>
    </li>
  );
};

const AcceptButton = (props: AcceptButtonProps): JSX.Element => {
  const Icon = acceptIcon;
  return (
    <button
      className="jp-button jp-pending-shares-listing-button"
      onClick={() => {
        void props.acceptShare(props.content);
      }}
    >
      <Icon.react
        className="jp-pending-shares-listing-icon jp-pending-shares-listing-accept"
        width="16px"
        height="16px"
      />
    </button>
  );
};

const RejectButton = (props: DeclineButtonProps): JSX.Element => {
  const Icon = declineIcon;
  return (
    <button
      className="jp-button jp-pending-shares-listing-button"
      onClick={() => {
        void props.declineShare(props.content);
      }}
    >
      <Icon.react
        className="jp-pending-shares-listing-icon jp-pending-shares-listing-reject"
        width="16px"
        height="16px"
      />
    </button>
  );
};
