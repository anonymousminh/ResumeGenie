'use client';

import { useState, ChangeEvent, FormEvent } from 'react';

export default function Home() {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobPostingText, setJobPostingText] = useState<string>('');
  const [parsedResumeContent, setParsedResumeContent] = useState<string>('');
  const [parsedJobPostingContent, setParsedJobPostingContent] = useState<string>('');
  const [rewrittenBullet, setRewrittenBullet] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleResumeFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setResumeFile(e.target.files[0]);
    }
  };

  const handleJobPostingTextChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setJobPostingText(e.target.value);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setParsedResumeContent('');
    setParsedJobPostingContent('');
    setRewrittenBullet('');

    if (!resumeFile || !jobPostingText) {
      setError("Please upload a resume and paste a job posting.");
      setLoading(false);
      return;
    }

    const reader = new FileReader();
    reader.readAsArrayBuffer(resumeFile);

    reader.onload = async (e) => {
      if (e.target && e.target.result) {
        const arrayBuffer = e.target.result as ArrayBuffer;
        const base64String = Buffer.from(arrayBuffer).toString("base64");

        try {
          // Step 1: Upload resume to S3 via backend endpoint
          const uploadResponse = await fetch("http://localhost:5000/upload_resume", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              resumeFileBase64: base64String,
              resumeFileName: resumeFile.name,
              resumeFileType: resumeFile.type,
              jobPostingText: jobPostingText,
            }),
          });

          if (!uploadResponse.ok) {
            const errorData = await uploadResponse.json();
            throw new Error(`Error uploading to S3: ${errorData.error}`);
          }

          const uploadData = await uploadResponse.json();
          const s3Url = uploadData.s3Url;
          console.log("File uploaded to S3:", s3Url);

          // Step 2: Call processing endpoint (parsing, embedding, saving to TiDB)
          const processResponse = await fetch("http://localhost:5000/process_documents", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              s3Url: s3Url,
              resumeFileType: resumeFile.type,
              jobPostingText: jobPostingText,
            }),
          });

          if (!processResponse.ok) {
            const errorData = await processResponse.json();
            throw new Error(`Error processing documents: ${errorData.error}`);
          }

          const processedData = await processResponse.json();
          setParsedResumeContent(processedData.parsedResumeText);
          setParsedJobPostingContent(processedData.parsedJobPostingText);
          console.log("Parsed Resume:", processedData.parsedResumeText.substring(0, 200) + "...");
          console.log("Parsed Job Posting:", processedData.parsedJobPostingText.substring(0, 200) + "...");
          console.log("Resume Embedding (first 5 dims):",


 processedData.resumeEmbedding.slice(0, 5), "...");
          console.log("Job Posting Embedding (first 5 dims):",


 processedData.jobPostingEmbedding.slice(0, 5), "...");

          // Example: Call the bullet rewriter for a sample bullet point
          // In a real app, you'd iterate through resume bullet points
          const sampleBullet = "Managed social media accounts."; // Replace with actual bullet from parsed resume
          const rewriteResponse = await fetch("http://localhost:5000/rewrite_bullet", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              bulletPoint: sampleBullet,
              jobDescription: jobPostingText,
            }),
          });

          if (!rewriteResponse.ok) {
            const errorData = await rewriteResponse.json();
            throw new Error(`Error rewriting bullet: ${errorData.error}`);
          }

          const rewriteData = await rewriteResponse.json();
          setRewrittenBullet(rewriteData.rewrittenBullet);
          console.log("Rewritten Bullet:", rewriteData.rewrittenBullet);

        } catch (err: unknown) {
          setError(err instanceof Error ? err.message : 'An unknown error occurred');
          console.error("Error during processing:", err);
        } finally {
          setLoading(false);
        }
      }
    };
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold mb-8">AI Career Coach / Resume Builder</h1>
      </div>

      <div className="relative z-10 flex flex-col items-center justify-center w-full max-w-3xl gap-6">
        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <div className="flex flex-col">
            <label htmlFor="resumeFile" className="mb-2 font-semibold">Upload Resume (PDF/DOCX):</label>
            <input
              type="file"
              id="resumeFile"
              accept=".pdf,.doc,.docx"
              onChange={handleResumeFileChange}
              className="p-2 border border-gray-300 rounded-md"
            />
          </div>

          <div className="flex flex-col">
            <label htmlFor="jobPostingText" className="mb-2 font-semibold">Paste Job Posting:</label>
            <textarea
              id="jobPostingText"
              rows={10}
              value={jobPostingText}
              onChange={handleJobPostingTextChange}
              placeholder="Paste the job description here..."
              className="p-2 border border-gray-300 rounded-md resize-y"
            ></textarea>
          </div>

          <button
            type="submit"
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md"
            disabled={loading}
          >
            {loading ? "Processing..." : "Analyze & Optimize Resume"}
          </button>
        </form>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative w-full" role="alert">
            <strong className="font-bold">Error:</strong>
            <span className="block sm:inline"> {error}</span>
          </div>
        )}

        {parsedResumeContent && parsedJobPostingContent && (
          <div className="w-full mt-8 p-6 border border-gray-200 rounded-md shadow-lg bg-white">
            <h2 className="text-2xl font-bold mb-4">Analysis Results</h2>
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2">Parsed Resume Content:</h3>
              <p className="bg-gray-50 p-3 rounded-md text-gray-700 whitespace-pre-wrap max-h-60 overflow-y-auto">
                {parsedResumeContent}
              </p>
            </div>
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2">Parsed Job Posting Content:</h3>
              <p className="bg-gray-50 p-3 rounded-md text-gray-700 whitespace-pre-wrap max-h-60 overflow-y-auto">
                {parsedJobPostingContent}
              </p>
            </div>
            {rewrittenBullet && (
              <div className="mb-4">
                <h3 className="text-xl font-semibold mb-2">Rewritten Sample Bullet Point:</h3>
                <p className="bg-green-50 p-3 rounded-md text-green-800 whitespace-pre-wrap">
                  {rewrittenBullet}
                </p>
              </div>
            )}
            {/* Placeholder for similarity score, skill suggestions, etc. */}
          </div>
        )}
      </div>
    </main>
  );
}