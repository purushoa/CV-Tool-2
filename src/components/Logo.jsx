import {blankCV,sampleCV,templates,steps} from '../data';
import React,{createContext,useContext,useEffect,useMemo,useRef,useState} from 'react';
import{createRoot}from'react-dom/client';
import{BrowserRouter,Routes,Route,Link,NavLink,useNavigate,useParams,Navigate}from'react-router-dom';
import{ArrowRight,ArrowLeft,Check,CheckCircle2,ChevronDown,ChevronRight,Copy,Download,FileText,Home,UserRound,Settings,Plus,Trash2,Eye,Edit3,Search,Menu,X,ShieldCheck,Star,LayoutTemplate,LogOut,Mail,Phone,MapPin,Globe,UploadCloud,Save,Palette,BriefcaseBusiness,GraduationCap,GripVertical,Lock,EyeOff,Clock,Monitor,Smartphone,PenLine, Sparkles}from'lucide-react';
import {useStore} from '../store/CVStore';
export function Logo({light=false}){return <Link to="/" className="inline-flex items-center gap-2.5 font-extrabold text-xl tracking-tight"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white"><FileText size={22}/></span><span className={light?'text-white':'text-slate-900'}>CV <span className="text-blue-600">Tool</span></span></Link>}
