import React from "react";
import {templates} from "../data";
const fmt=v=>{if(!v)return "";if(/^\d{4}-\d{2}$/.test(String(v))){const[y,m]=v.split("-");return new Date(+y,+m-1).toLocaleDateString("en-US",{month:"short",year:"numeric"})}return String(v)};
function Section({title,children}){return <section className="cv-section"><h2 className="cv-section-heading">{title}</h2>{children}</section>}
export function Resume({cv,innerRef}){
 const p=cv?.personal||{},selected=cv?.selected||{},type=cv?.template||"modern";
 const t=templates.find(x=>x.id===type)||templates[0],accent=cv?.accent||t.accent;
 const visible=k=>selected[k]!==false;
 const sidebar=["creative","coral","slate","emerald"].includes(type);
 const ats=t.category==="ATS-Friendly";
 const list=(key)=>Array.isArray(cv?.[key])?cv[key]:[];
 const experience=list("experience").filter(x=>!cv?.hiddenExperiences?.includes(x.id));
 const photo=t.photo?(p.photo?<img className="cv-profile-photo" src={p.photo} alt="Profile"/>:<div className="cv-profile-photo cv-photo-placeholder">{(p.fullName||"CV").split(" ").map(x=>x[0]).slice(0,2).join("").toUpperCase()}</div>):null;
 const heading=<header className="cv-header">{photo}<div><h1 className="cv-full-name">{p.fullName||"Your Name"}</h1><div className="cv-contact-details">{[p.email,p.phone,p.address,p.website].filter(Boolean).map((x,i)=><span key={i}>{x}</span>)}</div></div></header>;
 const summary=visible("summary")&&p.summary&&<Section title="Professional Summary"><p className="whitespace-pre-line">{p.summary}</p></Section>;
 const work=visible("experience")&&experience.length>0&&<Section title="Work Experience">{experience.map((x,i)=><div className="cv-entry" key={x.id||i}><div className="cv-entry-top"><strong>{x.title||"Position"}{x.company?` · ${x.company}`:""}</strong><small>{fmt(x.start)}{x.start||x.end||x.current?" – ":""}{x.current?"Present":fmt(x.end)}</small></div>{x.description&&<p className="whitespace-pre-line">{x.description}</p>}</div>)}</Section>;
 const education=visible("education")&&list("education").length>0&&<Section title="Education">{list("education").map((x,i)=><div className="cv-entry" key={x.id||i}><div className="cv-entry-top"><strong>{x.degree||"Qualification"}</strong><small>{fmt(x.start)}{x.start||x.end?" – ":""}{fmt(x.end)}</small></div><p>{x.school}</p></div>)}</Section>;
 const skills=visible("skills")&&list("skills").length>0&&<Section title="Skills">{ats?<p>{list("skills").join(" • ")}</p>:<div className="cv-skill-tags">{list("skills").map((x,i)=><span key={i}>{x}</span>)}</div>}</Section>;
 const languages=visible("languages")&&list("languages").length>0&&<Section title="Languages"><p>{list("languages").join(" • ")}</p></Section>;
 const projects=visible("projects")&&list("projects").length>0&&<Section title="Projects">{list("projects").map((x,i)=><div className="cv-entry" key={x.id||i}><strong>{x.title}</strong><p className="whitespace-pre-line">{x.description}</p></div>)}</Section>;
 const certs=visible("certifications")&&list("certifications").length>0&&<Section title="Certifications">{list("certifications").map((x,i)=><p key={x.id||i}>{typeof x==="string"?x:x.title||x.name}</p>)}</Section>;
 return <article ref={innerRef} className={`resume-sheet cv-template cv-${type}`} style={{"--cv-accent":accent,fontFamily:["classic","heritage"].includes(type)?"Georgia,serif":cv?.font==="Georgia"?"Georgia,serif":cv?.font==="Arial"?"Arial,sans-serif":"Inter,sans-serif"}}>{sidebar?<div className="cv-layout-sidebar"><aside className="cv-sidebar">{heading}{skills}{languages}</aside><main className="cv-main-content">{summary}{work}{education}{projects}{certs}</main></div>:<div className="cv-layout-standard">{heading}{summary}{work}{education}{skills}{languages}{projects}{certs}</div>}</article>;
}
