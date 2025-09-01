'use client';

import { useState, useEffect } from 'react';

interface ResumePreviewProps {
  resumeContent: string;
  jobPostingContent: string;
  onBulletSelect: (bulletPoint: string) => void;
}

export default function ResumePreview({ resumeContent, jobPostingContent, onBulletSelect }: ResumePreviewProps) {
  const [selectedBullet, setSelectedBullet] = useState<string>('');

  // Monitor when resumeContent changes
  useEffect(() => {
    console.log("ResumePreview: resumeContent changed");
    console.log("ResumePreview received content length:", resumeContent?.length);
    console.log("ResumePreview content preview:", resumeContent?.substring(0, 100));
  }, [resumeContent]);

  console.log("ResumePreview received content length:", resumeContent?.length);
  console.log("ResumePreview content preview:", resumeContent?.substring(0, 100));

  // Function to extract bullet points from resume content
  const extractBulletPoints = (content: string): string[] => {
    console.log("=== BULLET POINT EXTRACTION DEBUG ===");
    console.log("Input content length:", content?.length);
    console.log("Input content preview:", content?.substring(0, 500));
    
    if (!content || content.length === 0) {
      console.log("No content provided, returning empty array");
      return [];
    }
    
    // Split by common bullet point indicators
    const lines = content.split('\n');
    console.log("Total lines found:", lines.length);
    
    const bulletPoints: string[] = [];
    
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      
      // Skip empty lines
      if (!trimmedLine) return;
      
      console.log(`Line ${index}: "${trimmedLine}"`);
      
      // Skip obvious PDF metadata (but be less strict)
      if (
        trimmedLine.includes('<<') || 
        trimmedLine.includes('/Linearized') ||
        trimmedLine.startsWith('%PDF') ||
        trimmedLine.match(/^[<>\/\[\]\d\s]+$/) // Only skip if ALL symbols/numbers
      ) {
        console.log(`Line ${index}: Skipped (PDF metadata)`);
        return;
      }
      
      // Skip very short or very long lines
      if (trimmedLine.length < 3 || trimmedLine.length > 500) {
        console.log(`Line ${index}: Skipped (length: ${trimmedLine.length})`);
        return;
      }
      
      // Look for potential bullet points - more inclusive criteria
      const isBulletPoint = 
        // Traditional bullet points
        trimmedLine.startsWith('•') ||
        trimmedLine.startsWith('-') ||
        trimmedLine.startsWith('*') ||
        trimmedLine.startsWith('○') ||
        trimmedLine.startsWith('▪') ||
        trimmedLine.startsWith('▫') ||
        // Numbered lists
        trimmedLine.match(/^\d+\.\s/) ||
        trimmedLine.match(/^[a-z]\.\s/) ||
        // Action verbs (common in resumes)
        trimmedLine.match(/^[A-Z][a-z]+ed\s/) || // Past tense verbs
        trimmedLine.match(/^[A-Z][a-z]+ing\s/) || // Present participle
        trimmedLine.match(/^[A-Z][a-z]+s\s/) || // Present tense
        // Lines starting with capitalized words (likely sentences)
        trimmedLine.match(/^[A-Z][a-z]+\s/) ||
        // Lines with reasonable length that don't look like metadata
        (trimmedLine.length > 10 && trimmedLine.length < 400 && 
         !trimmedLine.match(/^[^a-zA-Z]*$/) && // Contains at least one letter
         trimmedLine.includes(' ')); // Contains spaces (likely a sentence)
      
      if (isBulletPoint) {
        // Clean up the bullet point
        const cleanBullet = trimmedLine.replace(/^[•\-*○▪▫]\s*/, '').trim();
        if (cleanBullet.length > 3) {
          bulletPoints.push(cleanBullet);
          console.log(`Line ${index}: ADDED as bullet point: "${cleanBullet}"`);
        }
      } else {
        console.log(`Line ${index}: Not a bullet point`);
      }
    });
    
    console.log("Final bullet points found:", bulletPoints.length);
    console.log("Bullet points:", bulletPoints);
    console.log("=== END DEBUG ===");
    
    return bulletPoints.slice(0, 20); // Increase limit to 20
  };

  // Alternative simpler bullet point extraction for testing
  const extractSimpleBulletPoints = (content: string): string[] => {
    if (!content) return [];
    
    const lines = content.split('\n');
    const bulletPoints: string[] = [];
    
    lines.forEach((line) => {
      const trimmedLine = line.trim();
      if (trimmedLine && trimmedLine.startsWith('•')) {
        const cleanBullet = trimmedLine.replace(/^•\s*/, '').trim();
        if (cleanBullet.length > 0) {
          bulletPoints.push(cleanBullet);
        }
      }
    });
    
    return bulletPoints;
  };

  const bulletPoints = extractBulletPoints(resumeContent);
  const simpleBulletPoints = extractSimpleBulletPoints(resumeContent);

  const handleBulletClick = (bullet: string) => {
    setSelectedBullet(bullet);
    onBulletSelect(bullet);
  };

  if (!resumeContent) {
    return (
      <div className="p-4 border rounded-lg">
        <h3 className="font-bold">Resume Preview</h3>
        <p className="text-gray-500">Upload a resume to see bullet points for rewriting.</p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="font-bold mb-4">Resume Bullet Points</h3>
      <p className="text-sm text-gray-600 mb-4">Click on any bullet point to get rewriting suggestions:</p>
      
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {bulletPoints.length > 0 ? (
          bulletPoints.map((bullet, index) => (
            <div
              key={index}
              className={`p-3 border rounded-md cursor-pointer transition-colors ${
                selectedBullet === bullet
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
              onClick={() => handleBulletClick(bullet)}
            >
              <p className="text-sm">{bullet}</p>
            </div>
          ))
        ) : (
          <div className="text-gray-500 text-sm">
            <p>No bullet points found in the resume.</p>
            <p className="mt-2">Debug info:</p>
            <p>Content length: {resumeContent?.length || 0}</p>
            <p>Content preview: {resumeContent?.substring(0, 200)}...</p>
            <p>Simple extraction found: {simpleBulletPoints.length} bullet points</p>
            {simpleBulletPoints.length > 0 && (
              <div className="mt-2 p-2 bg-yellow-50 border rounded">
                <p className="text-xs font-medium">Simple extraction results:</p>
                {simpleBulletPoints.map((bullet, index) => (
                  <p key={index} className="text-xs">• {bullet}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      
      {selectedBullet && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm font-medium text-blue-800">Selected:</p>
          <p className="text-sm text-blue-700 mt-1">{selectedBullet}</p>
        </div>
      )}
    </div>
  );
}