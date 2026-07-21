import { useState } from "react";
import { assessFiles } from "../api";
import ResultCard from "./ResultCard.jsx";

export default function AssessPanel({ courses, intakes }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  function onFiles(e) {
    setFiles(Array.from(e.target.files));
    setResult(null);
    setError(null);
  }

  async function run() {
    if (!files.length) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await assessFiles(files);
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel">
      <h2>Check an applicant</h2>
      <p className="muted">
        Upload the applicant's documents as PDF or JPG. The agent reads them and checks whether
        they meet the University of Salford entrance requirements for the chosen PGT course.
      </p>

      <div className="doc-checklist">
        <strong>Required documents (per admissions process):</strong>
        <ol>
          <li>PGT course choice — Course, Code, Year of Entry, Month of Entry</li>
          <li>Formal degree certificate</li>
          <li>Academic transcript (modules and grades)</li>
          <li>English language evidence (IELTS or equivalent, if not exempt)</li>
        </ol>
      </div>

      <label className="dropzone">
        <input type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={onFiles} />
        <div className="dz-inner">
          <span className="dz-icon">📁</span>
          <span>{files.length ? `${files.length} document(s) selected` : "Click to select documents (PDF / JPG)"}</span>
        </div>
      </label>

      {files.length > 0 && (
        <ul className="filelist">
          {files.map((f) => (
            <li key={f.name}>{f.name} <span className="muted">({Math.round(f.size / 1024)} KB)</span></li>
          ))}
        </ul>
      )}

      <button className="primary" disabled={!files.length || loading} onClick={run}>
        {loading ? "Checking documents…" : "Check documents"}
      </button>

      {error && <div className="alert error">{error}</div>}
      {result && <ResultCard result={result} />}

      {!result && courses?.length > 0 && (
        <div className="criteria-ref">
          <h3>Entrance requirements</h3>
          {courses.map((c) => (
            <div className="crit-row" key={c.admission_code}>
              <strong>{c.name}</strong>
              <span>{c.requirement}</span>
              {c.intake_months && (
                <span className="intake-note">Intakes: {c.intake_months.join(", ")}</span>
              )}
            </div>
          ))}
          <p className="english-note">All courses: IELTS 6.0 overall, no band below 5.5 (waived for majority English-speaking countries).</p>
          {intakes?.length > 0 && (
            <p className="english-note">Open intakes: {intakes.join(", ")}.</p>
          )}
        </div>
      )}
    </div>
  );
}
