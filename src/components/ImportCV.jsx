
import React, { useRef, useState } from 'react';
import { UploadCloud, FileText, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useStore } from '../store/CVStore';
import { readCVFile, parseCVText } from '../utils/importCV';

export default function ImportCV() {
  const inputRef = useRef(null);
  const navigate = useNavigate();
  const { setCVs, setToast } = useStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [draft, setDraft] = useState(null);

  async function handleFile(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setError('');
    setDraft(null);

    try {
      const text = await readCVFile(file);
      const imported = parseCVText(text, file.name);
      setDraft(imported);
    } catch (err) {
      setError(err.message || 'Import failed.');
    } finally {
      setLoading(false);
      event.target.value = '';
    }
  }

  function openEditor() {
    if (!draft) return;

    setCVs(previous => [draft, ...previous]);
    setToast('CV imported. Please review the extracted details.');
    navigate(`/builder/${draft.id}`);
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx"
        className="hidden"
        onChange={handleFile}
      />

      <button
        type="button"
        className="btn-outline"
        disabled={loading}
        onClick={() => inputRef.current?.click()}
      >
        <UploadCloud size={18} />
        {loading ? 'Reading CV...' : 'Import Existing CV'}
      </button>

      {error && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {draft && (
        <div className="panel mt-4 max-w-lg p-5">
          <div className="flex items-center justify-between">
            <h3 className="flex items-center gap-2 font-bold">
              <FileText size={18} />
              Imported CV
            </h3>

            <button onClick={() => setDraft(null)}>
              <X size={18} />
            </button>
          </div>

          <p className="mt-3 text-sm">
            <b>Name:</b> {draft.personal.fullName || 'Not detected'}
          </p>

          <p className="mt-1 text-sm">
            <b>Email:</b> {draft.personal.email || 'Not detected'}
          </p>

          <p className="mt-1 text-sm">
            <b>Experience:</b> {draft.experience.length} entries
          </p>

          <p className="mt-1 text-sm">
            <b>Education:</b> {draft.education.length} entries
          </p>

          <p className="mt-3 text-xs text-amber-700">
            Please review all extracted information.
            Automatic parsing may miss some details.
          </p>

          <button
            className="btn-primary mt-4"
            onClick={openEditor}
          >
            Open in CV Editor
          </button>
        </div>
      )}
    </div>
  );
}
