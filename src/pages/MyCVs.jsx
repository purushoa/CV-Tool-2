import {blankCV,sampleCV,templates,steps} from '../data';
import React,{createContext,useContext,useEffect,useMemo,useRef,useState} from 'react';
import{createRoot}from'react-dom/client';
import{BrowserRouter,Routes,Route,Link,NavLink,useNavigate,useParams,Navigate}from'react-router-dom';
import{ArrowRight,ArrowLeft,Check,CheckCircle2,ChevronDown,ChevronRight,Copy,Download,FileText,Home,UserRound,Settings,Plus,Trash2,Eye,Edit3,Search,Menu,X,ShieldCheck,Star,LayoutTemplate,LogOut,Mail,Phone,MapPin,Globe,UploadCloud,Save,Palette,BriefcaseBusiness,GraduationCap,GripVertical,Lock,EyeOff,Clock,Monitor,Smartphone,PenLine, Sparkles}from'lucide-react';
import {useStore} from '../store/CVStore';
import {Logo,Header,MiniResume,Footer,Sidebar,Workspace,CVGrid,Resume,PreviewPanel,TextField,TextArea,TagInput} from '../components/Shared';
export default function MyCVs(){const{cvs,createCV}=useStore();const nav=useNavigate();const[query,setQuery]=useState('');return <Workspace title="My CVs" subtitle="All your CVs, organized in one place." action={<button className="btn-primary" onClick={()=>nav(`/builder/${createCV()}`)}><Plus size={17}/> New CV</button>}><div className="relative mb-6 max-w-sm"><Search size={18} className="absolute left-4 top-3.5 text-slate-400"/><input className="field pl-11" placeholder="Search your CVs..." value={query} onChange={e=>setQuery(e.target.value)}/></div><CVGrid cvs={cvs.filter(c=>c.name.toLowerCase().includes(query.toLowerCase()))} onCreate={()=>nav(`/builder/${createCV()}`)}/></Workspace>}
