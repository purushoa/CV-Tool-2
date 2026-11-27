import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter,Routes,Route,Navigate} from 'react-router-dom';
import {CheckCircle2} from 'lucide-react';
import {StoreProvider,useStore} from './store/CVStore';
import HomePage from './pages/HomePage';
import TemplatesPage from './pages/TemplatesPage';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import MyCVs from './pages/MyCVs';
import Information from './pages/Information';
import SettingsPage from './pages/SettingsPage';
import Builder from './pages/CVBuilder';
import './index.css';
function Toast(){const{toast}=useStore();return toast?<div role="status" className="fixed bottom-6 right-6 z-50 flex max-w-sm items-center gap-3 rounded-xl bg-slate-900 px-5 py-4 text-sm font-semibold text-white shadow-xl"><CheckCircle2 className="text-green-400" size={18}/>{toast}</div>:null}
function App(){return <StoreProvider><BrowserRouter><Routes><Route path="/" element={<HomePage/>}/><Route path="/templates" element={<TemplatesPage/>}/><Route path="/login" element={<AuthPage/>}/><Route path="/signup" element={<AuthPage signup/>}/><Route path="/dashboard" element={<Dashboard/>}/><Route path="/my-cvs" element={<MyCVs/>}/><Route path="/information" element={<Information/>}/><Route path="/settings" element={<SettingsPage/>}/><Route path="/builder/:id" element={<Builder/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Routes><Toast/></BrowserRouter></StoreProvider>}
createRoot(document.getElementById('root')).render(<App/>);
