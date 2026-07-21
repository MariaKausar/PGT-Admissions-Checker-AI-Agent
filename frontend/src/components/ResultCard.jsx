function checkIcon(passed) {
  if (passed === true) return <span className="ck pass">✓</span>;
  if (passed === false) return <span className="ck fail">✕</span>;
  return <span className="ck unknown">?</span>;
}

const DECISION_LABELS = {
  ACCEPT: "MEETS REQUIREMENTS",
  REJECT: "DOES NOT MEET REQUIREMENTS",
  REVIEW: "NEEDS MANUAL REVIEW",
  INCOMPLETE: "MORE DOCUMENTS NEEDED",
};

export default function ResultCard({ result }) {
  const e = result.extracted || {};
  const decisionClass = result.decision?.toLowerCase();
  const label = DECISION_LABELS[result.decision] || result.decision;

  const missingCheck = result.checks?.find(
    (c) => c.name === "Required documents (brief)" && c.passed === null
  );
  const missingItems = missingCheck
    ? missingCheck.detail.replace(/^Missing:\s*/, "").split(";").map((s) => s.trim()).filter(Boolean)
    : [];

  return (
    <div className="result">
      <div className={`decision ${decisionClass}`}>
        <span className="decision-label">{label}</span>
        {result.course_matched && <span className="decision-course">{result.course_matched}</span>}
        {result.confidence && result.confidence !== "n/a" && (
          <span className="decision-conf">confidence: {result.confidence}</span>
        )}
      </div>

      <p className="summary">{result.summary}</p>

      {result.decision === "INCOMPLETE" && missingItems.length > 0 && (
        <div className="needed-box">
          <strong>Please request these documents from the applicant:</strong>
          <ul>
            {missingItems.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="staff-note">Advisory recommendation for admissions staff — not an automatic offer or rejection.</p>

      <h3>Entrance requirement checks</h3>
      <ul className="checks">
        {result.checks?.map((c, i) => (
          <li key={i}>
            {checkIcon(c.passed)}
            <div>
              <strong>{c.name}</strong>
              <p>{c.detail}</p>
            </div>
          </li>
        ))}
      </ul>

      <details className="extracted">
        <summary>Data extracted from applicant file</summary>
        <div className="grid">
          <Field label="Applicant" value={e.applicant_name} />
          <Field label="Course" value={e.course_name} />
          <Field label="Admission code" value={e.admission_code} />
          <Field label="Entry" value={[e.month_of_entry, e.year_of_entry].filter(Boolean).join(" ")} />
          <Field label="Degree" value={e.degree_title} />
          <Field label="Subject" value={e.degree_subject} />
          <Field label="Country" value={e.awarding_country} />
          <Field label="UK class" value={e.uk_classification} />
          <Field label="Percentage" value={e.percentage != null ? `${e.percentage}%` : null} />
          <Field label="CGPA" value={e.cgpa != null ? `${e.cgpa}${e.cgpa_scale ? " / " + e.cgpa_scale : ""}` : null} />
          <Field label="IELTS overall" value={e.ielts?.overall} />
          <Field label="First lang. English" value={e.first_language_english == null ? null : String(e.first_language_english)} />
        </div>
        {e.ielts && (
          <div className="grid">
            <Field label="Listening" value={e.ielts.listening} />
            <Field label="Reading" value={e.ielts.reading} />
            <Field label="Writing" value={e.ielts.writing} />
            <Field label="Speaking" value={e.ielts.speaking} />
          </div>
        )}
        {e.modules?.length > 0 && (
          <div className="modules">
            <strong>Modules</strong>
            <ul>
              {e.modules.map((m, i) => (
                <li key={i}>{m.name}{m.grade ? ` — ${m.grade}` : ""}</li>
              ))}
            </ul>
          </div>
        )}
        {e.extraction_notes && <p className="notes">Notes: {e.extraction_notes}</p>}
      </details>
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="field">
      <span className="flabel">{label}</span>
      <span className="fvalue">{value != null && value !== "" ? value : "—"}</span>
    </div>
  );
}
