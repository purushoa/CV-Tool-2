
import { templates, steps } from "../data";
import React, { useEffect, useRef, useState } from "react";

import {
  Link,
  useNavigate,
  useParams
} from "react-router-dom";

import {
  ArrowRight,
  ArrowLeft,
  Check,
  CheckCircle2,
  Download,
  Plus,
  Trash2,
  Eye,
  UploadCloud
} from "lucide-react";

import { useStore } from "../store/CVStore";

import {
  Logo,
  MiniResume,
  Resume,
  PreviewPanel,
  TextField,
  TextArea,
  TagInput
} from "../components/Shared";

import SectionOrder from "../components/SectionOrder";
import { exportWord } from "../utils/exportWord";

const uid = () => crypto.randomUUID();

export default function Builder() {
  const { id } = useParams();
  const nav = useNavigate();

  const {
    cvs,
    createCV,
    updateCV,
    setToast
  } = useStore();

  const [step, setStep] = useState(0);
  const [previewOpen, setPreviewOpen] = useState(false);

  const cv = cvs.find(x => x.id === id);

  useEffect(() => {
    if (id === "new") {
      const newId = createCV();

      const template = new URLSearchParams(
        window.location.search
      ).get("template");

      if (templates.some(x => x.id === template)) {
        updateCV(newId, c => ({
          ...c,
          template
        }));
      }

      nav(`/builder/${newId}`, {
        replace: true
      });
    }
  }, [id]);

  if (!cv) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <h1 className="text-2xl font-bold">
          CV not found
        </h1>

        <Link
          className="btn-primary"
          to="/dashboard"
        >
          Back to dashboard
        </Link>
      </div>
    );
  }

  const patch = fn => updateCV(cv.id, fn);

  const field = (key, value) =>
    patch(c => ({
      ...c,
      personal: {
        ...c.personal,
        [key]: value
      }
    }));

  const changeArray = (key, arr) =>
    patch(c => ({
      ...c,
      [key]: arr
    }));

  const updateEntry = (
    key,
    itemId,
    field,
    value
  ) =>
    changeArray(
      key,
      cv[key].map(x =>
        x.id === itemId
          ? { ...x, [field]: value }
          : x
      )
    );

  const addEntry = (key, obj) =>
    changeArray(key, [
      ...cv[key],
      { id: uid(), ...obj }
    ]);

  const removeEntry = (key, itemId) =>
    changeArray(
      key,
      cv[key].filter(x => x.id !== itemId)
    );

  const goNext = () => {
    setStep(s =>
      Math.min(s + 1, steps.length - 1)
    );
    window.scrollTo(0, 0);
  };

  const goBack = () => {
    setStep(s => Math.max(s - 1, 0));
    window.scrollTo(0, 0);
  };

  return (
    <div className="min-h-screen bg-[#f7f9fd]">

      {/* HEADER */}

      <div className="sticky top-0 z-20 border-b bg-white">
        <div className="mx-auto flex h-20 max-w-[1600px] items-center justify-between gap-4 px-5 lg:px-9">

          <div className="flex items-center gap-5">
            <Logo />

            <Link
              to="/dashboard"
              className="hidden items-center gap-1 text-sm font-semibold text-slate-500 hover:text-blue-600 md:flex"
            >
              <ArrowLeft size={16} />
              Dashboard
            </Link>
          </div>

          <div className="hidden text-center lg:block">
            <p className="text-sm font-bold">
              {cv.name}
            </p>

            <p className="mt-1 flex items-center justify-center gap-1 text-xs text-emerald-600">
              <CheckCircle2 size={13} />
              Saved in browser
            </p>
          </div>

          <div className="flex gap-2">
            <button
              className="btn-outline px-3 py-2 text-sm lg:hidden"
              onClick={() =>
                setPreviewOpen(!previewOpen)
              }
            >
              <Eye size={17} />
              Preview
            </button>

            <button
              className="btn-primary px-3 py-2 text-sm"
              onClick={() => setStep(6)}
            >
              <Download size={16} />
              Export
            </button>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-4 py-7 lg:px-9">

        {/* STEP NAVIGATION */}

        <div className="mb-7 flex flex-wrap items-center gap-2">
          {steps.map((s, i) => (
            <button
              key={s.key}
              onClick={() => setStep(i)}
              title={s.label}
              className={`flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold transition ${
                i === step
                  ? "bg-blue-600 text-white"
                  : i < step
                  ? "bg-blue-100 text-blue-700"
                  : "bg-white text-slate-400 hover:text-blue-600"
              }`}
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/20">
                {i < step ? (
                  <Check size={13} />
                ) : (
                  i + 1
                )}
              </span>

              <span className="hidden sm:inline">
                {s.label}
              </span>
            </button>
          ))}
        </div>

        <div className="grid items-start gap-7 xl:grid-cols-[minmax(0,1fr)_470px]">

          <div className="panel min-w-0 p-6 sm:p-8">

            {/* STEP TITLE */}

            <div className="mb-8 flex items-start justify-between gap-3">
              <div>
                <p className="mb-2 text-xs font-bold uppercase tracking-widest text-blue-600">
                  Step {step + 1} of {steps.length}
                </p>

                <h1 className="text-2xl font-extrabold text-slate-900">
                  {steps[step].label}
                </h1>

                <p className="mt-2 text-sm text-slate-500">
                  {
                    [
                      "Start with your contact details and a strong introduction.",
                      "Showcase the roles and results that matter most.",
                      "Highlight your qualifications and key strengths.",
                      "Add projects, languages, and certifications.",
                      "Choose and arrange exactly what appears on your CV.",
                      "Make your CV look and feel like you.",
                      "Review your CV and download it as a PDF or editable Word document."
                    ][step]
                  }
                </p>
              </div>
            </div>

            {/* STEP 1: PERSONAL DETAILS */}

            {step === 0 && (
              <div className="space-y-6">

                <TextField
                  label="CV name"
                  value={cv.name}
                  onChange={v =>
                    patch(c => ({ ...c, name: v }))
                  }
                  placeholder="e.g. Marketing CV"
                />

                <div className="grid gap-5 sm:grid-cols-2">

                  <TextField
                    label="Full name"
                    value={cv.personal.fullName}
                    onChange={v => field("fullName", v)}
                    placeholder="Alex Morgan"
                  />

                  <TextField
                    label="Email address"
                    type="email"
                    value={cv.personal.email}
                    onChange={v => field("email", v)}
                    placeholder="alex@example.com"
                  />

                  <TextField
                    label="Phone number"
                    value={cv.personal.phone}
                    onChange={v => field("phone", v)}
                    placeholder="+1 555 123 4567"
                  />

                  <TextField
                    label="Location / address"
                    value={cv.personal.address}
                    onChange={v => field("address", v)}
                    placeholder="City, Country"
                  />

                </div>

                <TextField
                  label="Portfolio / LinkedIn"
                  value={cv.personal.website}
                  onChange={v => field("website", v)}
                  placeholder="linkedin.com/in/yourname"
                />

                <TextArea
                  label="Professional summary"
                  value={cv.personal.summary}
                  onChange={v => field("summary", v)}
                  placeholder="Write 2–4 sentences about your strengths and experience..."
                  rows={5}
                />

                <div>
                  <label className="label">
                    Profile photo (optional)
                  </label>

                  <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-dashed border-blue-200 bg-blue-50 p-4 text-sm font-semibold text-blue-700">

                    <UploadCloud size={22} />

                    {cv.personal.photo
                      ? "Change profile photo"
                      : "Upload a profile photo"}

                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={e => {
                        const f = e.target.files?.[0];

                        if (!f) return;

                        if (f.size > 2 * 1024 * 1024) {
                          setToast(
                            "Please choose an image smaller than 2 MB"
                          );
                          return;
                        }

                        const reader = new FileReader();

                        reader.onload = () =>
                          field("photo", reader.result);

                        reader.readAsDataURL(f);
                      }}
                    />

                  </label>

                  {cv.personal.photo && (
                    <button
                      className="mt-2 text-xs font-bold text-red-500"
                      onClick={() => field("photo", "")}
                    >
                      Remove photo
                    </button>
                  )}
                </div>

              </div>
            )}

            {/* STEP 2: WORK EXPERIENCE */}

            {step === 1 && (
              <div className="space-y-5">

                {cv.experience.map((x, i) => (
                  <div
                    className="rounded-2xl border border-slate-200 p-5"
                    key={x.id}
                  >
                    <div className="mb-5 flex items-center justify-between">

                      <h3 className="font-bold">
                        Experience {i + 1}
                      </h3>

                      <button
                        className="text-red-500"
                        title="Remove experience"
                        onClick={() =>
                          removeEntry("experience", x.id)
                        }
                      >
                        <Trash2 size={18} />
                      </button>

                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">

                      <TextField
                        label="Job title"
                        value={x.title}
                        onChange={v =>
                          updateEntry(
                            "experience",
                            x.id,
                            "title",
                            v
                          )
                        }
                        placeholder="Software Engineer"
                      />

                      <TextField
                        label="Company"
                        value={x.company}
                        onChange={v =>
                          updateEntry(
                            "experience",
                            x.id,
                            "company",
                            v
                          )
                        }
                        placeholder="Company name"
                      />

                      <TextField
                        label="Start date"
                        type="month"
                        value={x.start}
                        onChange={v =>
                          updateEntry(
                            "experience",
                            x.id,
                            "start",
                            v
                          )
                        }
                      />

                      <TextField
                        label="End date"
                        type="month"
                        value={x.end}
                        onChange={v =>
                          updateEntry(
                            "experience",
                            x.id,
                            "end",
                            v
                          )
                        }
                      />

                    </div>

                    <label className="my-4 flex items-center gap-2 text-sm text-slate-600">

                      <input
                        type="checkbox"
                        checked={!!x.current}
                        onChange={e =>
                          updateEntry(
                            "experience",
                            x.id,
                            "current",
                            e.target.checked
                          )
                        }
                      />

                      I currently work here

                    </label>

                    <TextArea
                      label="Responsibilities & achievements"
                      value={x.description}
                      onChange={v =>
                        updateEntry(
                          "experience",
                          x.id,
                          "description",
                          v
                        )
                      }
                      placeholder="Describe your work and accomplishments..."
                    />

                  </div>
                ))}

                <button
                  className="btn-outline w-full border-dashed border-blue-300 text-blue-700"
                  onClick={() =>
                    addEntry("experience", {
                      title: "",
                      company: "",
                      start: "",
                      end: "",
                      current: false,
                      description: ""
                    })
                  }
                >
                  <Plus size={18} />
                  Add another experience
                </button>

              </div>
            )}

            {/* STEP 3: EDUCATION AND SKILLS */}

            {step === 2 && (
              <div className="space-y-7">

                <div>
                  <h3 className="mb-4 text-lg font-bold">
                    Education
                  </h3>

                  <div className="space-y-4">

                    {cv.education.map((x, i) => (
                      <div
                        key={x.id}
                        className="rounded-2xl border p-5"
                      >

                        <div className="mb-4 flex items-center justify-between">

                          <b>Education {i + 1}</b>

                          <button
                            className="text-red-500"
                            onClick={() =>
                              removeEntry("education", x.id)
                            }
                            title="Remove education"
                          >
                            <Trash2 size={17} />
                          </button>

                        </div>

                        <div className="grid gap-4 sm:grid-cols-2">

                          <TextField
                            label="Degree / qualification"
                            value={x.degree}
                            onChange={v =>
                              updateEntry(
                                "education",
                                x.id,
                                "degree",
                                v
                              )
                            }
                            placeholder="B.Sc. Computer Science"
                          />

                          <TextField
                            label="School / university"
                            value={x.school}
                            onChange={v =>
                              updateEntry(
                                "education",
                                x.id,
                                "school",
                                v
                              )
                            }
                            placeholder="University name"
                          />

                          <TextField
                            label="From year"
                            value={x.start}
                            onChange={v =>
                              updateEntry(
                                "education",
                                x.id,
                                "start",
                                v
                              )
                            }
                            placeholder="2020"
                          />

                          <TextField
                            label="To year"
                            value={x.end}
                            onChange={v =>
                              updateEntry(
                                "education",
                                x.id,
                                "end",
                                v
                              )
                            }
                            placeholder="2024"
                          />

                        </div>
                      </div>
                    ))}

                    <button
                      className="btn-outline w-full border-dashed border-blue-300 text-blue-700"
                      onClick={() =>
                        addEntry("education", {
                          degree: "",
                          school: "",
                          start: "",
                          end: ""
                        })
                      }
                    >
                      <Plus size={17} />
                      Add education
                    </button>

                  </div>
                </div>

                <div>
                  <h3 className="mb-4 text-lg font-bold">
                    Skills
                  </h3>

                  <TagInput
                    label="Skills"
                    values={cv.skills}
                    onChange={v =>
                      changeArray("skills", v)
                    }
                    placeholder="e.g. React, Communication, Excel"
                  />
                </div>

              </div>
            )}

            {/* STEP 4: MORE SECTIONS */}

            {step === 3 && (
              <div className="space-y-7">

                <div>
                  <h3 className="mb-4 text-lg font-bold">
                    Languages
                  </h3>

                  <TagInput
                    label="Languages"
                    values={cv.languages}
                    onChange={v =>
                      changeArray("languages", v)
                    }
                    placeholder="e.g. English, Finnish, Spanish"
                  />
                </div>

                {[
                  [
                    "projects",
                    "Projects",
                    "Project name",
                    "Project description"
                  ],
                  [
                    "certifications",
                    "Certifications",
                    "Certificate name",
                    null
                  ]
                ].map(
                  ([key, title, placeholder, detail]) => (
                    <div key={key}>

                      <h3 className="mb-4 text-lg font-bold">
                        {title}
                      </h3>

                      <div className="space-y-4">

                        {cv[key].map((x, i) => (
                          <div
                            key={x.id}
                            className="rounded-2xl border p-5"
                          >

                            <div className="mb-4 flex justify-between">

                              <b>
                                {title.slice(0, -1)} {i + 1}
                              </b>

                              <button
                                className="text-red-500"
                                title="Remove"
                                onClick={() =>
                                  removeEntry(key, x.id)
                                }
                              >
                                <Trash2 size={17} />
                              </button>

                            </div>

                            <TextField
                              label="Title"
                              value={x.title}
                              onChange={v =>
                                updateEntry(
                                  key,
                                  x.id,
                                  "title",
                                  v
                                )
                              }
                              placeholder={placeholder}
                            />

                            {detail && (
                              <div className="mt-4">

                                <TextArea
                                  label="Description"
                                  value={x.description}
                                  onChange={v =>
                                    updateEntry(
                                      key,
                                      x.id,
                                      "description",
                                      v
                                    )
                                  }
                                  placeholder={detail}
                                />

                              </div>
                            )}

                          </div>
                        ))}

                        <button
                          className="btn-outline w-full border-dashed border-blue-300 text-blue-700"
                          onClick={() =>
                            addEntry(key, {
                              title: "",
                              description: ""
                            })
                          }
                        >
                          <Plus size={17} />
                          Add {title.slice(0, -1).toLowerCase()}
                        </button>

                      </div>
                    </div>
                  )
                )}

              </div>
            )}

            {/* STEP 5: SELECT CONTENT AND REORDER */}

            {step === 4 && (
              <div className="space-y-5">

                <p className="text-sm text-slate-500">
                  Toggle sections to include or exclude
                  them from your finished CV.
                </p>

                {/* DRAG AND DROP SECTION ORDER */}

                <SectionOrder
                  cv={cv}
                  onChange={sectionOrder =>
                    patch(c => ({
                      ...c,
                      sectionOrder
                    }))
                  }
                />

                <h3 className="pt-3 text-lg font-bold">
                  Section visibility
                </h3>

                {[
                  ["personal", "Personal information"],
                  ["summary", "Professional summary"],
                  ["experience", "Work experience"],
                  ["education", "Education"],
                  ["skills", "Skills"],
                  ["languages", "Languages"],
                  ["projects", "Projects"],
                  ["certifications", "Certifications"]
                ].map(([key, label]) => (
                  <div
                    key={key}
                    className="rounded-xl border border-slate-200 p-4"
                  >

                    <label className="flex cursor-pointer items-center justify-between">

                      <span className="font-semibold">
                        {label}
                      </span>

                      <input
                        type="checkbox"
                        checked={
                          cv.selected?.[key] !== false
                        }
                        onChange={e =>
                          patch(c => ({
                            ...c,
                            selected: {
                              ...c.selected,
                              [key]: e.target.checked
                            }
                          }))
                        }
                      />

                    </label>

                    {key === "experience" &&
                      cv.selected?.experience !== false &&
                      cv.experience.length > 0 && (
                        <div className="mt-4 space-y-2 border-t pt-3">

                          {cv.experience.map(x => (
                            <label
                              key={x.id}
                              className="flex items-center gap-3 text-sm text-slate-500"
                            >

                              <input
                                type="checkbox"
                                checked={
                                  !cv.hiddenExperiences?.includes(
                                    x.id
                                  )
                                }
                                onChange={e =>
                                  patch(c => ({
                                    ...c,
                                    hiddenExperiences:
                                      e.target.checked
                                        ? (
                                            c.hiddenExperiences ||
                                            []
                                          ).filter(
                                            id => id !== x.id
                                          )
                                        : [
                                            ...(
                                              c.hiddenExperiences ||
                                              []
                                            ),
                                            x.id
                                          ]
                                  }))
                                }
                              />

                              {x.title || "Untitled role"}
                              {" — "}
                              {x.company || "Company"}

                            </label>
                          ))}

                        </div>
                      )}

                  </div>
                ))}

              </div>
            )}

            {/* STEP 6: CHOOSE TEMPLATE */}

            {step === 5 && (
              <div className="space-y-8">

                <div>
                  <h3 className="mb-4 text-lg font-bold">
                    Choose your template
                  </h3>

                  <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">

                    {templates.map(t => (
                      <button
                        key={t.id}
                        onClick={() =>
                          patch(c => ({
                            ...c,
                            template: t.id,
                            accent: t.accent
                          }))
                        }
                        className={`flex flex-col items-center rounded-xl border-2 p-3 transition ${
                          cv.template === t.id
                            ? "border-blue-600 bg-blue-50"
                            : "border-slate-100 hover:border-blue-200"
                        }`}
                      >

                        <div
                          className="origin-top scale-[.65]"
                          style={{ height: 150 }}
                        >
                          <MiniResume type={t.id} small />
                        </div>

                        <span className="mt-2 text-sm font-bold">
                          {t.name}
                        </span>

                        {cv.template === t.id && (
                          <CheckCircle2
                            className="mt-1 text-blue-600"
                            size={16}
                          />
                        )}

                      </button>
                    ))}

                  </div>
                </div>

                <div>
                  <label className="label">
                    Accent color
                  </label>

                  <div className="flex flex-wrap gap-3">

                    {[
                      "#2563eb",
                      "#0f766e",
                      "#7c3aed",
                      "#be123c",
                      "#111827",
                      "#ea580c"
                    ].map(c => (
                      <button
                        key={c}
                        aria-label={`Choose color ${c}`}
                        onClick={() =>
                          patch(x => ({
                            ...x,
                            accent: c
                          }))
                        }
                        className={`flex h-10 w-10 items-center justify-center rounded-full ${
                          cv.accent === c
                            ? "ring-2 ring-offset-2 ring-blue-500"
                            : ""
                        }`}
                        style={{ background: c }}
                      >

                        {cv.accent === c && (
                          <Check
                            size={18}
                            className="text-white"
                          />
                        )}

                      </button>
                    ))}

                  </div>
                </div>

                <div>
                  <label className="label">
                    Font style
                  </label>

                  <select
                    className="field"
                    value={cv.font || "Inter"}
                    onChange={e =>
                      patch(c => ({
                        ...c,
                        font: e.target.value
                      }))
                    }
                  >
                    <option>Inter</option>
                    <option>Arial</option>
                    <option>Georgia</option>
                  </select>
                </div>

              </div>
            )}

            {/* STEP 7: PREVIEW AND EXPORT */}

            {step === 6 && (
              <ExportPanel
                cv={cv}
                setToast={setToast}
              />
            )}

            {/* NAVIGATION BUTTONS */}

            <div className="mt-9 flex flex-wrap justify-between gap-3 border-t pt-6">

              <button
                className="btn-outline"
                onClick={
                  step === 0
                    ? () => nav("/dashboard")
                    : goBack
                }
              >
                <ArrowLeft size={17} />

                {step === 0 ? "Dashboard" : "Back"}
              </button>

              {step < 6 && (
                <button
                  className="btn-primary"
                  onClick={goNext}
                >
                  Continue
                  <ArrowRight size={17} />
                </button>
              )}

            </div>
          </div>

          {/* LIVE CV PREVIEW */}

          <aside
            className={`${
              previewOpen ? "block" : "hidden"
            } xl:sticky xl:top-28 xl:block`}
          >

            <div className="panel p-5">

              <div className="mb-5 flex items-center justify-between">

                <div>
                  <h3 className="font-bold">
                    Live CV preview
                  </h3>

                  <p className="mt-1 text-xs text-slate-400">
                    Updates automatically as you type
                  </p>
                </div>

                <span className="rounded-lg bg-green-50 px-2 py-1 text-xs font-bold text-green-700">
                  LIVE
                </span>

              </div>

              <div className="flex justify-center overflow-hidden">
                <PreviewPanel cv={cv} scale={0.49} />
              </div>

              <button
                className="btn-outline mt-5 w-full text-sm"
                onClick={() => setStep(6)}
              >
                <Eye size={17} />
                Full preview & export
              </button>

            </div>
          </aside>

        </div>
      </div>
    </div>
  );
}


/* PDF AND WORD EXPORT FUNCTIONS */

function ExportPanel({ cv, setToast }) {
  const [fileName, setFileName] = useState(
    (cv.personal.fullName || cv.name || "My_CV")
      .replace(/\s+/g, "_") + "_CV"
  );

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const resumeRef = useRef(null);

  /* READ DEFAULT EXPORT FORMAT */

  let preferredFormat = cv.exportFormat || "pdf";

  try {
    const savedPreferences = JSON.parse(
      localStorage.getItem("cvtool_preferences")
    );

    if (
      savedPreferences?.exportFormat === "pdf" ||
      savedPreferences?.exportFormat === "docx"
    ) {
      preferredFormat = savedPreferences.exportFormat;
    }
  } catch {
    // Keep the existing default format
  }

  const preferWord = preferredFormat === "docx";


  /* WORD EXPORT FUNCTION */

  const downloadWord = async () => {
    if (busy) return;

    setBusy(true);
    setError("");

    try {
      await exportWord(cv, fileName);

      setToast("Word CV download started");

    } catch (e) {

      console.error("Word export failed:", e);

      setError(
        e?.message ||
        "Could not export Word document"
      );

      setToast("Could not export Word document");

    } finally {

      setBusy(false);

    }
  };


  /* PDF EXPORT FUNCTION */

  const download = async () => {
    if (busy) return;

    setBusy(true);
    setError("");

    let host;

    try {
      const source = resumeRef.current;

      if (!source) {
        throw new Error(
          "CV preview is not available."
        );
      }

      host = document.createElement("div");

      host.className = "cv-pdf-export-host";

      host.style.cssText =
        "position:fixed;left:-10000px;top:0;width:794px;background:#fff;z-index:-1;";

      const copy = source.cloneNode(true);

      copy.style.transform = "none";
      copy.style.boxShadow = "none";
      copy.style.width = "794px";
      copy.style.minHeight = "1123px";

      host.appendChild(copy);
      document.body.appendChild(host);

      await Promise.all(
        Array.from(copy.querySelectorAll("img")).map(
          img =>
            img.complete
              ? Promise.resolve()
              : new Promise(resolve => {
                  img.onload = resolve;
                  img.onerror = resolve;
                })
        )
      );

      if (document.fonts?.ready) {
        await document.fonts.ready;
      }

      const { default: html2pdf } =
        await import("html2pdf.js");

      const safeName =
        (
          fileName
            .trim()
            .replace(/\.(pdf|docx)$/i, "")
            .replace(/[<>:"/\\|?*\x00-\x1f]/g, "_") ||
          "My_CV"
        ) + ".pdf";

      await html2pdf()
        .set({
          margin: 0,

          filename: safeName,

          image: {
            type: "jpeg",
            quality: 0.98
          },

          html2canvas: {
            scale: 2,
            useCORS: true,
            backgroundColor: "#ffffff",
            scrollX: 0,
            scrollY: 0,
            windowWidth: 794
          },

          jsPDF: {
            unit: "px",
            format: [794, 1123],
            orientation: "portrait",
            hotfixes: ["px_scaling"]
          },

          pagebreak: {
            mode: ["css", "legacy"],
            avoid: [".resume-entry", "header"]
          }
        })
        .from(copy)
        .save();

      setToast("CV PDF download started");

    } catch (e) {

      console.error("CV PDF export failed:", e);

      setError(
        e?.message ||
        "PDF export failed. Open the browser console for details."
      );

      setToast("Could not export PDF");

    } finally {

      host?.remove();
      setBusy(false);

    }
  };


  /* EXPORT PAGE UI */

  return (
    <div className="space-y-5">

      {/* SUCCESS MESSAGE */}

      <div className="rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm text-blue-700">

        <CheckCircle2
          size={17}
          className="mr-2 inline"
        />

        Your CV is ready to preview and export.

      </div>


      {/* FILE NAME */}

      <TextField
        label="File name"
        value={fileName}
        onChange={setFileName}
        placeholder="My_CV"
      />

      <p className="text-xs text-slate-500">
        Your browser chooses the download folder.
        Both files are generated locally.
      </p>


      {/* ERROR MESSAGE */}

      {error && (
        <p
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </p>
      )}


      {/* PREFERRED EXPORT FORMAT */}

      <div className="flex items-center justify-between gap-3 rounded-xl border border-blue-100 bg-blue-50 p-3">

        <span className="text-sm font-semibold text-blue-700">
          Preferred export format
        </span>

        <span className="rounded-lg bg-blue-600 px-3 py-1 text-xs font-bold text-white">

          {preferWord
            ? "Word (.docx)"
            : "PDF (.pdf)"}

        </span>

      </div>


      {/* PDF AND WORD DOWNLOAD BUTTONS */}

      <div className="grid gap-3 sm:grid-cols-2">

        {(preferWord
          ? ["docx", "pdf"]
          : ["pdf", "docx"]
        ).map(format => (

          <button
            key={format}
            type="button"
            className="btn-primary w-full"
            disabled={busy}
            onClick={
              format === "docx"
                ? downloadWord
                : download
            }
          >

            <Download size={18} />

            {busy
              ? "Preparing..."
              : format === "docx"
                ? "Download CV as Word (.docx)"
                : "Download CV as PDF"
            }

          </button>

        ))}

      </div>


      {/* FILE FORMAT INFORMATION */}

      <p className="text-center text-xs text-slate-500">
        PDF preserves your visual design.
        Word allows you to edit your CV after downloading.
      </p>


      {/* FULL CV PREVIEW */}

      <div className="mt-6">

        <h3 className="mb-4 font-bold">
          Full CV preview
        </h3>

        <div className="overflow-x-auto rounded-xl bg-slate-100 p-4">

          <div
            className="mx-auto"
            style={{ width: 794 }}
          >

            <Resume
              cv={cv}
              innerRef={resumeRef}
            />

          </div>

        </div>

      </div>

    </div>
  );
}
