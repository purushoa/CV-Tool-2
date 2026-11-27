
export const sectionLabels = {
  summary: "Professional Summary",
  experience: "Work Experience",
  education: "Education",
  skills: "Skills",
  languages: "Languages",
  projects: "Projects",
  certifications: "Certifications"
};

export const defaultSectionOrder = Object.keys(sectionLabels);

export function getSectionOrder(cv) {
  const saved = Array.isArray(cv?.sectionOrder)
    ? cv.sectionOrder
    : [];

  return [
    ...new Set([
      ...saved.filter(key => defaultSectionOrder.includes(key)),
      ...defaultSectionOrder
    ])
  ];
}

export function moveSection(order, from, to) {
  if (
    from < 0 ||
    to < 0 ||
    from >= order.length ||
    to >= order.length
  ) {
    return order;
  }

  const next = [...order];
  next.splice(to, 0, next.splice(from, 1)[0]);

  return next;
}
