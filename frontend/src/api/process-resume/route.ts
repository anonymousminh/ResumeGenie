import { NextResponse } from "next/server";

export async function POST(request: Request) {
    try {
        const formData = await request.formData();
        const resumeFile = formData.get("resumeFile") as File | null;
        const jobPostingText = formData.get("jobPostingText") as string;

        if (!resumeFile || !jobPostingText) {
            return NextResponse.json({ error: "Missing resume file or job posting text" }, { status: 400 });
        }

        console.log("Received resume file:", resumeFile.name);
        console.log("Received job posting text:", jobPostingText.substring(0, 100) + '...');

        return NextResponse.json({message: "Data received successfully!", resumeFileName: resumeFile.name});
    } catch (error) {
        console.error("Error processing request:", error);
        return NextResponse.json({error: "Internal Server Error"}, {status: 500});
    }
}