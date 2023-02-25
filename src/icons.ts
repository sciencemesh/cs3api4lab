import accept from '../style/icons/accept.svg';
import decline from '../style/icons/decline.svg';
import share from '../style/icons/share.svg';
import info from '../style/icons/info.svg';
import { LabIcon } from '@jupyterlab/ui-components';

export const acceptIcon = new LabIcon({
  name: 'cs3api4lab:accept',
  svgstr: accept
});

export const declineIcon = new LabIcon({
  name: 'cs3api4lab:decline',
  svgstr: decline
});

export const shareIcon = new LabIcon({
  name: 'cs3api4lab:share',
  svgstr: share
});

export const infoIcon = new LabIcon({
  name: 'cs3api4lab:info',
  svgstr: info
});
