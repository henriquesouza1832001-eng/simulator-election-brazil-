import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './styles.css';
import './views.css';
import './editorial.css';
import './readability.css';
import './theme.css';
import './polish.css';
import './government.css';

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>);
