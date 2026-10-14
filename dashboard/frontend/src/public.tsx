import React from 'react';
import {createRoot} from 'react-dom/client';
import PublicDashboard from './PublicDashboard';
import './style.css';
createRoot(document.getElementById('root')!).render(<React.StrictMode><PublicDashboard/></React.StrictMode>);
