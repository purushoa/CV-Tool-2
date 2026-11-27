import { createWorker } from 'tesseract.js';
import { blankCV } from '../data';

const sections = {
  summary: /^(professional summary|summary|profile|objective|about me)$/i,
  experience: /^(work experience|professional experience|experience|employment history)$/i,
  education: /^(education|academic background|qualifications)$/i,
  skills: /^(skills|technical skills|key skills|core competencies)$/i,
  languages: /^(languages|language skills)$/i,
  projects: /^(projects|selected projects)$/i,
  certifications: /^(certifications|certificates|licenses)$/i,
};

function splitItems(lines) {
  return lines.join('\n').split(/[,;•\n]+/)
    .map(s => s.trim()).filter(Boolean);
}

function entries(lines, type) {
  const groups = lines.join('\n').split(/\n\s*\n/)
    .map(s => s.trim()).filter(Boolean);

  return groups.map(group => {
    const [first, ...rest] = group.split('\n');
    const parts = first.split(/\s+[|–—-]\s+/);
    const id = crypto.randomUUID();

    if (type === 'education') {
      return {
        id, degree: parts[0] || '',
        school: parts[1] || '', start: '', end: ''
      };
    }
    if (type === 'experience') {
      return {
        id, title: parts[0] || '',
        company: parts[1] || '',
        start: '', end: '', current: false,
        description: rest.join('\n')
      };
    }
    return { id, title: first, description: rest.join('\n') };
  });
}

export function parseCVText(text, filename) {
  if (!text.trim()) {
    throw new Error(
      'No readable text found. Scanned PDFs need OCR.'
    );
  }

  const cv = blankCV();
  cv.name = filename.replace(/\.(pdf|docx)$/i, '');

  const groups = { intro: [] };
  let current = 'intro';

  for (const line of text.replace(/\r/g, '').split('\n')) {
    const clean = line.trim().replace(/:$/, '');
    const heading = Object.entries(sections)
      .find(([, regex]) => regex.test(clean));

    if (heading) {
      current = heading[0];
      groups[current] ??= [];
    } else {
      groups[current] ??= [];
      groups[current].push(line.trim());
    }
  }

  const email = text.match(
    /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i
  )?.[0] || '';

  const phone = text.match(
    /(?:\+?\d[\d\s().-]{7,}\d)/
  )?.[0] || '';

  const intro = groups.intro.filter(Boolean);
  const name = intro.find(line =>
    !line.includes('@') &&
    !/\d{5,}/.test(line) &&
    line.length < 70 &&
    !/^(resume|curriculum vitae)$/i.test(line)
  ) || '';

  cv.personal = {
    ...cv.personal,
    fullName: name,
    email,
    phone,
    summary: (groups.summary || []).join('\n')
  };

  cv.experience = entries(groups.experience || [], 'experience');
  cv.education = entries(groups.education || [], 'education');
  cv.skills = splitItems(groups.skills || []);
  cv.languages = splitItems(groups.languages || []);
  cv.projects = entries(groups.projects || [], 'projects');
  cv.certifications = entries(
    groups.certifications || [], 'certifications'
  );

  return cv;
}

export async function readCVFile(file) {
  if (file.size > 10 * 1024 * 1024) {
    throw new Error('Maximum file size is 10 MB.');
  }

  const name = file.name.toLowerCase();

  if (name.endsWith('.docx')) {
    const mammoth = await import('mammoth/mammoth.browser');
    const result = await mammoth.extractRawText({
      arrayBuffer: await file.arrayBuffer()
    });
    return result.value;
  }

  if (name.endsWith('.pdf')) {
    const pdfjs = await import('pdfjs-dist');
    const worker = await import(
      'pdfjs-dist/build/pdf.worker.min.mjs?url'
    );

    pdfjs.GlobalWorkerOptions.workerSrc = worker.default;

    const pdf = await pdfjs.getDocument({
      data: new Uint8Array(await file.arrayBuffer())
    }).promise;

    try {
      const pages = [];

      for (let n = 1; n <= pdf.numPages; n++) {
        const page = await pdf.getPage(n);
        const content = await page.getTextContent();

        const lines = [];
        let row = '';
        let previousY = null;

        for (const item of content.items) {
          if (!('str' in item)) continue;

          const y = item.transform?.[5];

          if (previousY !== null && Math.abs(y - previousY) > 3) {
            lines.push(row);
            row = '';
          }

          row += item.str + ' ';
          previousY = y;

          if (item.hasEOL) {
            lines.push(row);
            row = '';
            previousY = null;
          }
        }

        if (row.trim()) lines.push(row);
        pages.push(lines.join('\n'));
      }

      const extractedText = pages.join('\n\n').trim();

if (extractedText.length > 0) {
  return extractedText;
}

// No selectable text found, so use OCR.
return await extractScannedPDF(pdf);
    } finally {
      await pdf.destroy();
    }
  }

  throw new Error('Please upload a PDF or DOCX file.');
}

async function extractScannedPDF(pdf) {
  const worker = await createWorker('eng');
  const extractedPages = [];

  try {
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {
      const page = await pdf.getPage(pageNumber);

      const viewport = page.getViewport({ scale: 2 });

      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');

      canvas.width = Math.ceil(viewport.width);
      canvas.height = Math.ceil(viewport.height);

      await page.render({
        canvasContext: context,
        viewport
      }).promise;

      const result = await worker.recognize(canvas);

      extractedPages.push(result.data.text);

      canvas.width = 0;
      canvas.height = 0;
    }

    return extractedPages.join('\n\n');
  } finally {
    await worker.terminate();
  }
}
