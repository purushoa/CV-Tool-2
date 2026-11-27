export const blankCV=()=>({id:crypto.randomUUID(),name:'Untitled CV',template:'modern',accent:'#2563eb',font:'Inter',updatedAt:new Date().toISOString(),personal:{fullName:'',email:'',phone:'',address:'',website:'',summary:'',photo:''},experience:[],education:[],skills:[],languages:[],projects:[],certifications:[],selected:{personal:true,summary:true,experience:true,education:true,skills:true,languages:true,projects:true,certifications:true},hiddenExperiences:[]});
export const sampleCV=()=>({ ...blankCV(),name:'My Professional CV',personal:{fullName:'Alex Morgan',email:'alex.morgan@example.com',phone:'+1 (555) 123-4567',address:'New York, NY',website:'linkedin.com/in/alexmorgan',summary:'Detail-oriented professional with experience leading projects, collaborating across teams, and delivering measurable results.',photo:''},experience:[{id:'e1',title:'Marketing Specialist',company:'Northstar Studio',start:'2022-06',end:'',current:true,description:'Led cross-functional campaigns and improved customer engagement through data-driven content strategy.'},{id:'e2',title:'Marketing Intern',company:'Brightside Co.',start:'2021-01',end:'2022-05',current:false,description:'Supported campaign reporting, social media scheduling, and market research.'}],education:[{id:'ed1',degree:'B.A. Business Administration',school:'State University',start:'2017',end:'2021'}],skills:['Project Management','Communication','Microsoft Excel','Content Strategy'],languages:['English','Spanish'],projects:[{id:'p1',title:'Brand Refresh',description:'Coordinated a brand refresh across web and social channels.'}],certifications:[]});
export const templates = [
  {
    "id": "modern",
    "name": "Modern Blue",
    "category": "Modern",
    "desc": "Clean and professional design",
    "accent": "#2563eb",
    "photo": false
  },
  {
    "id": "executive",
    "name": "Executive",
    "category": "Modern",
    "desc": "Elegant corporate CV",
    "accent": "#1e3a8a",
    "photo": false
  },
  {
    "id": "skyline",
    "name": "Skyline",
    "category": "Modern",
    "desc": "Contemporary professional layout",
    "accent": "#0891b2",
    "photo": false
  },
  {
    "id": "classic",
    "name": "Classic",
    "category": "Classic",
    "desc": "Traditional formal CV",
    "accent": "#24304d",
    "photo": false
  },
  {
    "id": "heritage",
    "name": "Heritage",
    "category": "Classic",
    "desc": "Elegant serif typography",
    "accent": "#713f12",
    "photo": false
  },
  {
    "id": "creative",
    "name": "Creative Teal",
    "category": "Creative",
    "desc": "Fresh and distinctive design",
    "accent": "#0f766e",
    "photo": false
  },
  {
    "id": "coral",
    "name": "Coral Studio",
    "category": "Creative",
    "desc": "Colorful creative CV",
    "accent": "#e11d48",
    "photo": false
  },
  {
    "id": "portrait",
    "name": "Portrait Pro",
    "category": "With Photo",
    "desc": "Professional CV with profile photo",
    "accent": "#2563eb",
    "photo": true
  },
  {
    "id": "slate",
    "name": "Profile Slate",
    "category": "With Photo",
    "desc": "Dark sidebar with portrait",
    "accent": "#334155",
    "photo": true
  },
  {
    "id": "emerald",
    "name": "Emerald Photo",
    "category": "With Photo",
    "desc": "Elegant green photo CV",
    "accent": "#047857",
    "photo": true
  },
  {
    "id": "minimal",
    "name": "Minimal ATS",
    "category": "ATS-Friendly",
    "desc": "Simple single-column CV",
    "accent": "#111827",
    "photo": false
  },
  {
    "id": "ats-essential",
    "name": "ATS Essential",
    "category": "ATS-Friendly",
    "desc": "Clean recruitment-focused CV",
    "accent": "#111827",
    "photo": false
  },
  {
    "id": "ats-pro",
    "name": "ATS Professional",
    "category": "ATS-Friendly",
    "desc": "Structured professional CV",
    "accent": "#374151",
    "photo": false
  }
];
export const steps=[{key:'personal',label:'Personal Details'},{key:'experience',label:'Work Experience'},{key:'education',label:'Education & Skills'},{key:'additional',label:'More Sections'},{key:'content',label:'Select Content'},{key:'template',label:'Choose Template'},{key:'preview',label:'Preview & Export'}];
