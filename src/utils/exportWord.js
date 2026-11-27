
import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  AlignmentType,
  BorderStyle,
  HeadingLevel
} from "docx";

import { getSectionOrder } from "./sectionOrder";

export async function exportWord(cv, fileName) {

  const p = cv.personal || {};
  const selected = cv.selected || {};

  const accent = (cv.accent || "#2563eb")
    .replace("#", "");

  const font = cv.font || "Arial";

  const children = [];

  const visible = key =>
    selected[key] !== false;

  const list = key =>
    Array.isArray(cv[key]) ? cv[key] : [];

  const fmt = value => {
    if (!value) return "";

    if (/^\d{4}-\d{2}$/.test(value)) {
      const [year, month] = value.split("-");

      return new Date(
        Number(year),
        Number(month) - 1
      ).toLocaleDateString("en-US", {
        month: "short",
        year: "numeric"
      });
    }

    return String(value);
  };

  // SECTION HEADINGS

  const addHeading = title => {
    children.push(
      new Paragraph({
        heading: HeadingLevel.HEADING_2,

        spacing: {
          before: 280,
          after: 140
        },

        border: {
          bottom: {
            color: accent,
            space: 5,
            style: BorderStyle.SINGLE,
            size: 6
          }
        },

        children: [
          new TextRun({
            text: title.toUpperCase(),
            bold: true,
            color: accent,
            size: 24,
            font
          })
        ]
      })
    );
  };

  // NORMAL TEXT

  const addText = (value, bold = false) => {
    if (!value) return;

    String(value)
      .split(/\r?\n/)
      .forEach(line => {
        children.push(
          new Paragraph({
            spacing: {
              after: 100
            },

            children: [
              new TextRun({
                text: line,
                bold,
                font,
                size: 22,
                color: "334155"
              })
            ]
          })
        );
      });
  };

  // DATES

  const addDate = value => {
    if (!value) return;

    children.push(
      new Paragraph({
        spacing: {
          after: 100
        },

        children: [
          new TextRun({
            text: value,
            italics: true,
            color: "64748B",
            font,
            size: 20
          })
        ]
      })
    );
  };

  // PERSONAL INFORMATION

  if (visible("personal")) {

    children.push(
      new Paragraph({
        alignment: AlignmentType.CENTER,

        spacing: {
          after: 180
        },

        children: [
          new TextRun({
            text: p.fullName || "Your Name",
            bold: true,
            color: accent,
            size: 48,
            font
          })
        ]
      })
    );

    const contact = [
      p.email,
      p.phone,
      p.address,
      p.website
    ]
      .filter(Boolean)
      .join("  |  ");

    if (contact) {
      children.push(
        new Paragraph({
          alignment: AlignmentType.CENTER,

          spacing: {
            after: 300
          },

          children: [
            new TextRun({
              text: contact,
              color: "64748B",
              size: 20,
              font
            })
          ]
        })
      );
    }
  }

  // PROFESSIONAL SUMMARY

  const addSummary = () => {
    if (!visible("summary") || !p.summary) {
      return;
    }

    addHeading("Professional Summary");
    addText(p.summary);
  };

  // WORK EXPERIENCE

  const addExperience = () => {

    const experience = list("experience").filter(
      x => !cv.hiddenExperiences?.includes(x.id)
    );

    if (
      !visible("experience") ||
      experience.length === 0
    ) {
      return;
    }

    addHeading("Work Experience");

    experience.forEach(x => {

      addText(
        [x.title, x.company]
          .filter(Boolean)
          .join(" · "),
        true
      );

      const dates = [
        fmt(x.start),
        x.current ? "Present" : fmt(x.end)
      ]
        .filter(Boolean)
        .join(" – ");

      addDate(dates);

      addText(x.description);
    });
  };

  // EDUCATION

  const addEducation = () => {

    if (
      !visible("education") ||
      list("education").length === 0
    ) {
      return;
    }

    addHeading("Education");

    list("education").forEach(x => {

      addText(x.degree, true);

      addText(x.school);

      addDate(
        [fmt(x.start), fmt(x.end)]
          .filter(Boolean)
          .join(" – ")
      );
    });
  };

  // SKILLS

  const addSkills = () => {

    if (
      !visible("skills") ||
      list("skills").length === 0
    ) {
      return;
    }

    addHeading("Skills");

    addText(
      list("skills").join(" • ")
    );
  };

  // LANGUAGES

  const addLanguages = () => {

    if (
      !visible("languages") ||
      list("languages").length === 0
    ) {
      return;
    }

    addHeading("Languages");

    addText(
      list("languages").join(" • ")
    );
  };

  // PROJECTS

  const addProjects = () => {

    if (
      !visible("projects") ||
      list("projects").length === 0
    ) {
      return;
    }

    addHeading("Projects");

    list("projects").forEach(x => {

      addText(x.title, true);

      addText(x.description);
    });
  };

  // CERTIFICATIONS

  const addCertifications = () => {

    if (
      !visible("certifications") ||
      list("certifications").length === 0
    ) {
      return;
    }

    addHeading("Certifications");

    list("certifications").forEach(x => {

      addText(
        typeof x === "string"
          ? x
          : x.title || x.name
      );
    });
  };

  // CUSTOM DRAG AND DROP ORDER

  const sections = {
    summary: addSummary,
    experience: addExperience,
    education: addEducation,
    skills: addSkills,
    languages: addLanguages,
    projects: addProjects,
    certifications: addCertifications
  };

  const order = getSectionOrder(cv);

  order.forEach(key => {
    sections[key]?.();
  });

  // CREATE WORD DOCUMENT

  const doc = new Document({

    creator: "CV Tool",

    title: p.fullName
      ? `${p.fullName} - CV`
      : "My CV",

    description: "Generated using CV Tool",

    sections: [
      {
        properties: {
          page: {
            size: {
              width: 11906,
              height: 16838
            },

            margin: {
              top: 850,
              bottom: 850,
              left: 850,
              right: 850
            }
          }
        },

        children
      }
    ]
  });

  // GENERATE DOWNLOADABLE WORD FILE

  const blob = await Packer.toBlob(doc);

  const safeName =
    (
      (fileName || "My_CV")
        .trim()
        .replace(/\.(pdf|docx)$/i, "")
        .replace(/[<>:"/\\|?*\x00-\x1f]/g, "_")
      || "My_CV"
    ) + ".docx";

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;

  link.download = safeName;

  document.body.appendChild(link);

  link.click();

  link.remove();

  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 1000);
}
