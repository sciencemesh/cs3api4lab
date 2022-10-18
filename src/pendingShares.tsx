import { ReactWidget } from '@jupyterlab/apputils';
import * as React from 'react';
import { acceptIcon, declineIcon } from './icons';
import {
  AcceptButtonProps,
  DeclineButtonProps,
  PendingShareProp,
  PendingSharesContentProps
} from './types';
import { findFileIcon, requestAPI } from './services';
import { useEffect, useState } from 'react';
import { Time } from '@jupyterlab/coreutils';
import { Widget } from '@lumino/widgets';

export class PendingSharesListWrapper extends ReactWidget {
  constructor() {
    super();
    this.hide = this.hide.bind(this);
    this.show = this.show.bind(this);

    this.addClass('jp-pending-shares-listing-wrapper');
  }

  protected onResize(msg: Widget.ResizeMessage): void {
    const { width } =
      msg.width === -1 ? this.node.getBoundingClientRect() : msg;

    this.toggleClass('jp-pending-shares-narrow', width < 290);
  }

  protected render(): JSX.Element {
    return (
      <div>
        <PendingSharesContent hideWidget={this.hide} showWidget={this.show} />
      </div>
    );
  }
}

const PendingSharesContent = (
  props: PendingSharesContentProps
): JSX.Element => {
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

  useEffect((): void => {
    if (pendingShares.length > 0) {
      props.showWidget();
    }
  }, [pendingShares]);

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
