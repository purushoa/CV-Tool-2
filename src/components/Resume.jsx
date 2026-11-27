
import React from "react";
import { templates } from "../data";
import { getSectionOrder } from "../utils/sectionOrder";

// FORMAT DATES

const fmt = v => {
  if (!v) return "";

  if (/^\d{4}-\d{2}$/.test(String(v))) {
    const [y, m] = v.split("-");

    return new Date(+y, +m - 1).toLocaleDateString(
      "en-US",
      {
        month: "short",
        year: "numeric"
      }
    );
  }

  return String(v);
};

// SECTION COMPONENT

function Section({ title, children }) {
  return (
    <section className="cv-section">
      <h2 className="cv-section-heading">
        {title}
      </h2>

      {children}
    </section>
  );
}

// MAIN RESUME COMPONENT

export function Resume({ cv, innerRef }) {

  const p = cv?.personal || {};
  const selected = cv?.selected || {};
  const type = cv?.template || "modern";

  const t =
    templates.find(x => x.id === type) ||
    templates[0];

  const accent = cv?.accent || t.accent;

  const visible = key =>
    selected[key] !== false;

  // SIDEBAR TEMPLATES

  const sidebar = [
    "creative",
    "coral",
    "slate",
    "emerald"
  ].includes(type);

  const ats = t.category === "ATS-Friendly";

  const list = key =>
    Array.isArray(cv?.[key]) ? cv[key] : [];

  const experience = list("experience").filter(
    x => !cv?.hiddenExperiences?.includes(x.id)
  );

  // PROFILE PHOTO

  const photo = t.photo ? (
    p.photo ? (
      <img
        className="cv-profile-photo"
        src={p.photo}
        alt="Profile"
      />
    ) : (
      <div className="cv-profile-photo cv-photo-placeholder">

        {(p.fullName || "CV")
          .split(" ")
          .map(x => x[0])
          .slice(0, 2)
          .join("")
          .toUpperCase()}

      </div>
    )
  ) : null;

  // PERSONAL INFORMATION

  const heading = (
    <header className="cv-header">

      {photo}

      <div>

        <h1 className="cv-full-name">
          {p.fullName || "Your Name"}
        </h1>

        <div className="cv-contact-details">

          {[
            p.email,
            p.phone,
            p.address,
            p.website
          ]
            .filter(Boolean)
            .map((x, i) => (
              <span key={i}>
                {x}
              </span>
            ))}

        </div>

      </div>

    </header>
  );

  // PROFESSIONAL SUMMARY

  const summary =
    visible("summary") &&
    p.summary && (
      <Section title="Professional Summary">

        <p className="whitespace-pre-line">
          {p.summary}
        </p>

      </Section>
    );

  // WORK EXPERIENCE

  const work =
    visible("experience") &&
    experience.length > 0 && (
      <Section title="Work Experience">

        {experience.map((x, i) => (
          <div
            className="cv-entry"
            key={x.id || i}
          >

            <div className="cv-entry-top">

              <strong>

                {x.title || "Position"}

                {x.company
                  ? ` · ${x.company}`
                  : ""}

              </strong>

              <small>

                {fmt(x.start)}

                {x.start || x.end || x.current
                  ? " – "
                  : ""}

                {x.current
                  ? "Present"
                  : fmt(x.end)}

              </small>

            </div>

            {x.description && (
              <p className="whitespace-pre-line">
                {x.description}
              </p>
            )}

          </div>
        ))}

      </Section>
    );

  // EDUCATION

  const education =
    visible("education") &&
    list("education").length > 0 && (
      <Section title="Education">

        {list("education").map((x, i) => (
          <div
            className="cv-entry"
            key={x.id || i}
          >

            <div className="cv-entry-top">

              <strong>
                {x.degree || "Qualification"}
              </strong>

              <small>

                {fmt(x.start)}

                {x.start || x.end
                  ? " – "
                  : ""}

                {fmt(x.end)}

              </small>

            </div>

            <p>
              {x.school}
            </p>

          </div>
        ))}

      </Section>
    );

  // SKILLS

  const skills =
    visible("skills") &&
    list("skills").length > 0 && (
      <Section title="Skills">

        {ats ? (

          <p>
            {list("skills").join(" • ")}
          </p>

        ) : (

          <div className="cv-skill-tags">

            {list("skills").map((x, i) => (
              <span key={i}>
                {x}
              </span>
            ))}

          </div>

        )}

      </Section>
    );

  // LANGUAGES

  const languages =
    visible("languages") &&
    list("languages").length > 0 && (
      <Section title="Languages">

        <p>
          {list("languages").join(" • ")}
        </p>

      </Section>
    );

  // PROJECTS

  const projects =
    visible("projects") &&
    list("projects").length > 0 && (
      <Section title="Projects">

        {list("projects").map((x, i) => (
          <div
            className="cv-entry"
            key={x.id || i}
          >

            <strong>
              {x.title}
            </strong>

            <p className="whitespace-pre-line">
              {x.description}
            </p>

          </div>
        ))}

      </Section>
    );

  // CERTIFICATIONS

  const certs =
    visible("certifications") &&
    list("certifications").length > 0 && (
      <Section title="Certifications">

        {list("certifications").map((x, i) => (
          <p key={x.id || i}>

            {typeof x === "string"
              ? x
              : x.title || x.name}

          </p>
        ))}

      </Section>
    );

  // ==========================================
  // DRAG AND DROP SECTION ORDER
  // ==========================================

  const order = getSectionOrder(cv);

  const blocks = {
    summary: summary,
    experience: work,
    education: education,
    skills: skills,
    languages: languages,
    projects: projects,
    certifications: certs
  };

  // RENDER SECTIONS IN CUSTOM ORDER

  const renderOrder = keys =>
    keys.map(key => (
      <React.Fragment key={key}>
        {blocks[key]}
      </React.Fragment>
    ));

  // ==========================================
  // PRESERVE ORIGINAL SIDEBAR TEMPLATE DESIGN
  // ==========================================

  const sidebarSections = [
    "skills",
    "languages"
  ];

  const sidebarOrder = order.filter(
    key => sidebarSections.includes(key)
  );

  const mainOrder = order.filter(
    key => !sidebarSections.includes(key)
  );

  // ==========================================
  // FINAL CV RENDERING
  // ==========================================

  return (
    <article
      ref={innerRef}
      className={`resume-sheet cv-template cv-${type}`}
      style={{
        "--cv-accent": accent,

        fontFamily: [
          "classic",
          "heritage"
        ].includes(type)
          ? "Georgia,serif"
          : cv?.font === "Georgia"
          ? "Georgia,serif"
          : cv?.font === "Arial"
          ? "Arial,sans-serif"
          : "Inter,sans-serif"
      }}
    >

      {sidebar ? (

        /* TWO-COLUMN SIDEBAR TEMPLATES */

        <div className="cv-layout-sidebar">

          {/* LEFT SIDEBAR */}

          <aside className="cv-sidebar">

            {heading}

            {renderOrder(sidebarOrder)}

          </aside>

          {/* RIGHT MAIN CONTENT */}

          <main className="cv-main-content">

            {renderOrder(mainOrder)}

          </main>

        </div>

      ) : (

        /* STANDARD SINGLE-COLUMN TEMPLATES */

        <div className="cv-layout-standard">

          {heading}

          {renderOrder(order)}

        </div>

      )}

    </article>
  );
}
