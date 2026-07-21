import { useEffect, useState } from "react";
import { getCourses } from "./api";
import AssessPanel from "./components/AssessPanel.jsx";

export default function App() {
  const [courseData, setCourseData] = useState(null);

  useEffect(() => {
    getCourses().then(setCourseData).catch(() => setCourseData(null));
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">US</span>
          <div>
            <div className="title-row">
              <h1>PGT Admissions Checker</h1>
              <span className="staff-badge">Staff only</span>
            </div>
            <p>Upload an applicant's documents and check them against the entrance requirements</p>
          </div>
        </div>
      </header>

      <main className="layout-single">
        <AssessPanel courses={courseData?.courses} intakes={courseData?.open_intakes} />
      </main>
    </div>
  );
}
