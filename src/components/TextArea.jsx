import {blankCV,sampleCV,templates,steps} from '../data';
import React,{createContext,useContext,useEffect,useMemo,useRef,useState} from 'react';
import{createRoot}from'react-dom/client';
import{BrowserRouter,Routes,Route,Link,NavLink,useNavigate,useParams,Navigate}from'react-router-dom';
import{ArrowRight,ArrowLeft,Check,CheckCircle2,ChevronDown,ChevronRight,Copy,Download,FileText,Home,UserRound,Settings,Plus,Trash2,Eye,Edit3,Search,Menu,X,ShieldCheck,Star,LayoutTemplate,LogOut,Mail,Phone,MapPin,Globe,UploadCloud,Save,Palette,BriefcaseBusiness,GraduationCap,GripVertical,Lock,EyeOff,Clock,Monitor,Smartphone,PenLine, Sparkles}from'lucide-react';
import {useStore} from '../store/CVStore';
export function TextArea({label,value,onChange,placeholder='',rows=4}){return <div><label className="label">{label}</label><textarea rows={rows} className="field resize-y" value={value||''} onChange={e=>onChange(e.target.value)} placeholder={placeholder}/></div>}
