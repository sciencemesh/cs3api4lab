import React, {useState} from 'react';

type MenuProps = {
    tabHandler: (tabname: string) => void
}

const Menu = (props: MenuProps): JSX.Element => {
    const [activeTab, setActiveTab] = useState('info');

    return (<>
            <nav className='jp-file-info-menu'>
                <ul>
                    <li className={ activeTab == 'info' ? 'active' : ''} onClick={() => {
                        setActiveTab('info');
                        props.tabHandler('info')
                    }}>INFO</li>
                    <li className={ activeTab == 'share' ? 'active' : ''}  onClick={() => {
                        setActiveTab('share');
                        props.tabHandler('shares')
                    }}>SHARES</li>
                    <li>LINKS</li>
                </ul>
            </nav>
            <hr className='jp-file-info-menu-separator' />
        </>
    );
}

export default Menu;
