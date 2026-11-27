import {blankCV,sampleCV,templates,steps} from '../data';
import React,{createContext,useContext,useEffect,useMemo,useRef,useState} from 'react';
import{createRoot}from'react-dom/client';
import{BrowserRouter,Routes,Route,Link,NavLink,useNavigate,useParams,Navigate}from'react-router-dom';
import{ArrowRight,ArrowLeft,Check,CheckCircle2,ChevronDown,ChevronRight,Copy,Download,FileText,Home,UserRound,Settings,Plus,Trash2,Eye,Edit3,Search,Menu,X,ShieldCheck,Star,LayoutTemplate,LogOut,Mail,Phone,MapPin,Globe,UploadCloud,Save,Palette,BriefcaseBusiness,GraduationCap,GripVertical,Lock,EyeOff,Clock,Monitor,Smartphone,PenLine, Sparkles}from'lucide-react';
import {useStore} from '../store/CVStore';
import {Sidebar} from "./Sidebar";
export function Workspace({children,title,subtitle,action}){return <div className="min-h-screen bg-[#f8faff]"><Sidebar/><main className="min-h-screen p-5 pt-20 md:ml-64 md:p-9"><div className="mx-auto max-w-6xl"><div className="mb-8 flex flex-wrap items-center justify-between gap-4"><div><h1 className="text-3xl font-extrabold text-slate-900">{title}</h1><p className="mt-2 text-sm text-slate-500">{subtitle}</p></div>{action}</div>{children}</div></main></div>}
