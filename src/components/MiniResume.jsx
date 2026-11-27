import React from "react";
import {templates} from "../data";
export function MiniResume({type="modern",small=false}) {
 const t=templates.find(x=>x.id===type)||templates[0];
 const sidebar=["creative","coral","slate","emerald"].includes(type);
 const classic=["classic","heritage"].includes(type);
 const ats=t.category==="ATS-Friendly";
 const bars=(n=3,light=false)=><div className="space-y-1.5">{Array.from({length:n},(_,i)=><div key={i} className={`h-[3px] rounded ${light?"bg-white/40":"bg-slate-200"}`} style={{width:i%3===0?"90%":i%3===1?"72%":"83%"}}/>)}</div>;
 const section=(title,n=3,light=false)=><div className="mt-3"><div className={`mb-2 text-[7px] font-bold uppercase tracking-wider ${light?"text-white":""}`} style={light?{}:{color:t.accent}}>{title}</div>{bars(n,light)}</div>;
 return <div className={`cv-mini-preview relative overflow-hidden rounded-md border border-slate-200 bg-white shadow-lg ${small?"h-56 w-40":"h-[360px] w-[254px]"}`} style={{fontFamily:classic?"Georgia,serif":"Arial,sans-serif"}}>
 {sidebar?<div className="flex h-full"><aside className="w-[38%] p-3 text-white" style={{background:t.accent}}>{t.photo&&<div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white/80 text-sm font-bold text-slate-600">AM</div>}<b className="text-[10px] leading-tight">ALEX<br/>MORGAN</b><p className="mt-1 text-[6px] text-white/80">PROFESSIONAL</p>{section("Contact",3,true)}{section("Skills",5,true)}{section("Languages",2,true)}</aside><main className="w-[62%] p-3">{section("Profile",4)}{section("Experience",8)}{section("Education",4)}{section("Projects",3)}</main></div>:
 <div>{!classic&&!ats&&<div className="h-2" style={{background:t.accent}}/>}<div className="p-5">{t.photo&&<div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-200 text-sm font-bold text-slate-600">AM</div>}<div className={`font-bold ${small?"text-xs":"text-lg"} ${classic||t.photo?"text-center":""}`} style={{color:ats?"#111827":t.accent}}>ALEX MORGAN</div><div className={`mt-1 text-[7px] tracking-widest text-slate-400 ${classic||t.photo?"text-center":""}`}>MARKETING SPECIALIST</div><div className="my-3 h-px bg-slate-200"/>{bars(2)}{section("Profile",3)}{section("Experience",7)}{section("Education",3)}{section("Skills",4)}{!ats&&section("Languages",2)}</div></div>}</div>;
}
