'use client';

import { useState } from "react";
import SuggestionCard from "@/components/features/SuggestionCard";
import ResumePreview from "@/components/features/ResumePreview";

export default function Home() {

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobPostingText, setJobPostingText] = useState<string>("");
  const [resumeContent, setResumeContent] = useState<string>("");
  const [jobPostingContent, setJobPostingContent] = useState<string>("");
  
  const handleResumeFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setResumeFile(file);
      const reader = new FileReader();
      reader.onload = (e) => {  
        if (e.target && typeof e.target.result === 'string') {
          setResumeContent(e.target.result as string);
        }
      };
      reader.readAsText(file);
    }
  };

  const handleJobPostingTextChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setJobPostingText(event.target.value);
    setJobPostingContent(event.target.value);
  }

  const handleSubmit = async () => {
    if (!resumeFile || jobPostingText) {
      alert("Please upload a resume and paste the job posting.");
      return;
    }

    const formData = new FormData();
    formData.append("resumeFile", resumeFile);
    formData.append("jobPostingText", jobPostingText);

    try {
      const response = await fetch("/api/process-resume", {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Success: ${data.message}`);
        console.log(data);
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.error}`);
        console.log(errorData);
      } 
    } catch (error) {
      console.error("Failed to send data:", error);
      alert("An error occurred while sending data.");
    }
  };


  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          AI Career Coach / Resume Builder
        </p>
      </div>

      <div className="relative flex place-items-center before:absolute before:h-[300px] before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-[240px] after:translate-x-1/3 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-sky-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px] z-[-1]">
        <h1 className="text-4xl font-bold">Upload Your Resume and Job Posting</h1>
      </div>

      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-2 lg:text-left">
        {/* Resume Upload Section */}
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30">
          <h2 className={`mb-3 text-2xl font-semibold`}>
            Resume Upload
          </h2>
          <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeFileChange} className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100"/>
          {resumeFile && <p className="mt-2 text-sm text-gray-600">Selected File: {resumeFile.name}</p>}
          {resumeContent && (<div className="mt-4 p-2 border rounded-md bg-gray-50 max-h-40 overflow-y-auto text-sm">
            <h3 className="font-semibold">Resume Content Review</h3>
            <pre className="whitespace-pre-wrap">{resumeContent.substring(0, 500)}...</pre>
          </div>)}
        </div>

        {/* Job Posting Input Section */}
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30">
          <h2 className={`mb-3 text-2xl font-semibold`}>
            Job Posting
          </h2>
          <textarea
            className="w-full p-2 border rounded-md text-black bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={10}
            placeholder="Paste the job posting text here..."
            value={jobPostingText}
            onChange={handleJobPostingTextChange}
          ></textarea>
          {jobPostingContent && (
            <div className="mt-4 p-2 border rounded-md bg-gray-50 max-h-40 overflow-y-auto text-sm">
              <h3 className="font-semibold">Job Posting Content Preview:</h3>
              <pre className="whitespace-pre-wrap">{jobPostingContent.substring(0, 500)}...</pre>
            </div>
          )}
        </div>
      </div>

      <div className="mt-8 w-full flex justify-center">
        <button onClick={handleSubmit} className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">
          Analyze Resume
        </button>
      </div>

      <div className="mt-16 grid gap-8 lg:max-w-5xl lg:w-full lg:grid-cols-2">
        <SuggestionCard />
        <ResumePreview />
      </div>
    </main>
  );
}