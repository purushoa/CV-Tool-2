import {blankCV,sampleCV,templates,steps} from '../data';
import React,{createContext,useContext,useEffect,useMemo,useRef,useState} from 'react';
import{createRoot}from'react-dom/client';
import{BrowserRouter,Routes,Route,Link,NavLink,useNavigate,useParams,Navigate}from'react-router-dom';
import{ArrowRight,ArrowLeft,Check,CheckCircle2,ChevronDown,ChevronRight,Copy,Download,FileText,Home,UserRound,Settings,Plus,Trash2,Eye,Edit3,Search,Menu,X,ShieldCheck,Star,LayoutTemplate,LogOut,Mail,Phone,MapPin,Globe,UploadCloud,Save,Palette,BriefcaseBusiness,GraduationCap,GripVertical,Lock,EyeOff,Clock,Monitor,Smartphone,PenLine, Sparkles}from'lucide-react';
import {useStore} from '../store/CVStore';
import {Logo} from "./Logo";
export function Footer(){return <footer className="border-t bg-white"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-5 px-5 py-9 lg:px-8"><Logo/><p className="text-sm text-slate-500">© {new Date().getFullYear()} CV Tool. Build your future with confidence.</p><div className="flex gap-6 text-sm text-slate-500"><Link to="/templates">Templates</Link><Link to="/dashboard">Dashboard</Link></div></div></footer>}
