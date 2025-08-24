import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const resumeFile = formData.get("resumeFile") as File | null;
    const jobPostingText = formData.get("jobPostingText") as string;

    if (!resumeFile || !jobPostingText) {
      return NextResponse.json({ error: "Missing resume file or job posting text" }, { status: 400 });
    }

    // For now, just log the received data. The actual S3 upload will happen in the Python backend.
    console.log("Received resume file:", resumeFile.name);
    console.log("Received job posting text:", jobPostingText.substring(0, 100) + "...");

    // In later steps, we will integrate LangChain here to process the data

    return NextResponse.json({ message: "Data received successfully!", resumeFileName: resumeFile.name });
  } catch (error) {
    console.error("Error processing request:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}