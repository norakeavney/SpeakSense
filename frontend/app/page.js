'use client';

import { useState } from 'react';
import AudioUpload from '../components/AudioUpload';
import AnalysisProgress from '../components/AnalysisProgress';
import Dashboard from '../components/Dashboard';

export default function HomePage() {
  const [stage, setStage] = useState("upload");
  const [jobId, setJobId] = useState(null);
  const [analysisData, setAnalysisData] = useState(null);

  return (
    <main>
      {stage === "upload" && (
        <AudioUpload
          onUploadComplete={(response) => {
            setJobId(response.job_id);
            setStage("processing");
          }}
        />
      )}

      {stage === "processing" && (
        <AnalysisProgress
          jobId={jobId}
          onComplete={(data) => {
            console.log("ANALYSIS COMPLETE:", data);
            setAnalysisData(data);
            setStage("dashboard");
          }}
        />
      )}

      {stage === "dashboard" && (
        <Dashboard data={analysisData} />
      )}
    </main>
  );
}