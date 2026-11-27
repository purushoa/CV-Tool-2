import {blankCV,sampleCV,templates,steps} from '../data';
import React,{createContext,useContext,useEffect,useMemo,useRef,useState} from 'react';
import{createRoot}from'react-dom/client';
import{BrowserRouter,Routes,Route,Link,NavLink,useNavigate,useParams,Navigate}from'react-router-dom';
import{ArrowRight,ArrowLeft,Check,CheckCircle2,ChevronDown,ChevronRight,Copy,Download,FileText,Home,UserRound,Settings,Plus,Trash2,Eye,Edit3,Search,Menu,X,ShieldCheck,Star,LayoutTemplate,LogOut,Mail,Phone,MapPin,Globe,UploadCloud,Save,Palette,BriefcaseBusiness,GraduationCap,GripVertical,Lock,EyeOff,Clock,Monitor,Smartphone,PenLine, Sparkles}from'lucide-react';
import {useStore} from '../store/CVStore';
import {Resume} from "./Resume";
export function PreviewPanel({cv,scale=.52}){return <div className="overflow-hidden rounded-xl border border-slate-200 bg-slate-100 p-4"><div className="mx-auto overflow-hidden" style={{width:`${794*scale}px`,height:`${1123*scale}px`,maxWidth:'100%'}}><div style={{transform:`scale(${scale})`,transformOrigin:'top left'}}><Resume cv={cv}/></div></div></div>}
