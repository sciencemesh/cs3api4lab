import accept from '../style/icons/accept.svg';
import decline from '../style/icons/decline.svg';
import { LabIcon } from '@jupyterlab/ui-components';

export const acceptIcon = new LabIcon({
  name: 'cs3api4lab:accept',
  svgstr: accept
});

export const declineIcon = new LabIcon({
  name: 'cs3api4lab:decline',
  svgstr: decline
});
