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
    console.log("ResumePreview FULL content:", resumeContent);
  }, [resumeContent]);

  console.log("ResumePreview received content length:", resumeContent?.length);
  console.log("ResumePreview content preview:", resumeContent?.substring(0, 100));
  console.log("ResumePreview FULL content:", resumeContent);

  // Function to extract bullet points from resume content
  const extractBulletPoints = (content: string): string[] => {
    console.log("=== BULLET POINT EXTRACTION DEBUG ===");
    console.log("Input content length:", content?.length);
    console.log("Input content preview:", content?.substring(0, 500));
    
    if (!content || content.length === 0) {
      console.log("No content provided, returning empty array");
      return [];
    }
    
    const bulletPoints: string[] = [];
    
    // Method 1: Try traditional line-by-line extraction first
    const lines = content.split('\n');
    console.log("Total lines found:", lines.length);
    
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      
      // Skip empty lines
      if (!trimmedLine) return;
      
      console.log(`Line ${index}: "${trimmedLine}"`);
      
      // Skip obvious PDF metadata
      if (
        trimmedLine.includes('<<') || 
        trimmedLine.includes('/Linearized') ||
        trimmedLine.startsWith('%PDF') ||
        trimmedLine.match(/^[<>\/\[\]\d\s]+$/)
      ) {
        console.log(`Line ${index}: Skipped (PDF metadata)`);
        return;
      }
      
      // Skip very short or very long lines
      if (trimmedLine.length < 3 || trimmedLine.length > 500) {
        console.log(`Line ${index}: Skipped (length: ${trimmedLine.length})`);
        return;
      }
      
      // Look for traditional bullet points
      const isTraditionalBullet = 
        trimmedLine.startsWith('•') ||
        trimmedLine.startsWith('-') ||
        trimmedLine.startsWith('*') ||
        trimmedLine.startsWith('○') ||
        trimmedLine.startsWith('▪') ||
        trimmedLine.startsWith('▫') ||
        trimmedLine.match(/^\d+\.\s/) ||
        trimmedLine.match(/^[a-z]\.\s/);
      
      if (isTraditionalBullet) {
        const cleanBullet = trimmedLine.replace(/^[•\-*○▪▫]\s*/, '').trim();
        if (cleanBullet.length > 3) {
          bulletPoints.push(cleanBullet);
          console.log(`Line ${index}: ADDED as traditional bullet: "${cleanBullet}"`);
        }
      }
    });
    
    // Method 2: If no traditional bullets found, try smart content parsing
    if (bulletPoints.length === 0) {
      console.log("No traditional bullets found, trying smart content parsing...");
      
      // Split content into sentences and look for action-oriented statements
      const sentences = content
        .split(/[.!?]\s+/)
        .map(s => s.trim())
        .filter(s => s.length > 10 && s.length < 300);
      
      console.log("Found sentences:", sentences.length);
      
      sentences.forEach((sentence, index) => {
        console.log(`Sentence ${index}: "${sentence}"`);
        
        // Look for action verbs and achievement-oriented language
        const actionVerbs = [
          'developed', 'created', 'built', 'designed', 'implemented', 'managed', 'led', 'coordinated',
          'analyzed', 'optimized', 'improved', 'increased', 'decreased', 'reduced', 'enhanced',
          'collaborated', 'communicated', 'presented', 'delivered', 'achieved', 'accomplished',
          'maintained', 'supported', 'assisted', 'trained', 'mentored', 'supervised',
          'researched', 'investigated', 'evaluated', 'assessed', 'monitored', 'tracked',
          'programmed', 'coded', 'debugged', 'tested', 'deployed', 'configured',
          'automated', 'streamlined', 'integrated', 'migrated', 'upgraded', 'refactored'
        ];
        
        const hasActionVerb = actionVerbs.some(verb => 
          sentence.toLowerCase().includes(verb.toLowerCase())
        );
        
        // Look for quantifiable achievements (numbers, percentages, etc.)
        const hasQuantifiable = /\d+/.test(sentence);
        
        // Look for professional keywords
        const professionalKeywords = [
          'project', 'team', 'client', 'customer', 'user', 'system', 'application',
          'database', 'software', 'technology', 'framework', 'platform', 'service',
          'process', 'workflow', 'solution', 'strategy', 'initiative', 'program'
        ];
        
        const hasProfessionalKeyword = professionalKeywords.some(keyword =>
          sentence.toLowerCase().includes(keyword.toLowerCase())
        );
        
        // Skip contact info, education headers, etc.
        const isContactInfo = /^(phone|email|address|linkedin|github|portfolio|education|university|gpa|expected|bachelor|master|degree)/i.test(sentence);
        const isHeader = sentence.length < 50 && /^[A-Z\s]+$/.test(sentence);
        
        if (!isContactInfo && !isHeader && (hasActionVerb || hasQuantifiable || hasProfessionalKeyword)) {
          bulletPoints.push(sentence);
          console.log(`Sentence ${index}: ADDED as smart bullet: "${sentence}"`);
        } else {
          console.log(`Sentence ${index}: Skipped (${isContactInfo ? 'contact info' : isHeader ? 'header' : 'no action/professional content'})`);
        }
      });
    }
    
    // Method 3: If still no bullets, try extracting from experience sections
    if (bulletPoints.length === 0) {
      console.log("No smart bullets found, trying experience section extraction...");
      
      // Look for experience/work sections and extract content
      const experienceKeywords = ['experience', 'work', 'employment', 'projects', 'achievements'];
      const sections = content.split(/\n\s*\n/);
      
      sections.forEach((section, index) => {
        const lowerSection = section.toLowerCase();
        const isExperienceSection = experienceKeywords.some(keyword => 
          lowerSection.includes(keyword)
        );
        
        if (isExperienceSection) {
          console.log(`Section ${index}: Found experience section`);
          // Extract sentences from this section
          const sectionSentences = section
            .split(/[.!?]\s+/)
            .map(s => s.trim())
            .filter(s => s.length > 15 && s.length < 250);
          
          sectionSentences.forEach(sentence => {
            if (sentence.length > 15 && !bulletPoints.includes(sentence)) {
              bulletPoints.push(sentence);
              console.log(`Added from experience section: "${sentence}"`);
            }
          });
        }
      });
    }
    
    console.log("Final bullet points found:", bulletPoints.length);
    console.log("Bullet points:", bulletPoints);
    console.log("=== END DEBUG ===");
    
    return bulletPoints.slice(0, 25); // Return up to 25 bullet points
  };

  // Alternative simpler bullet point extraction for testing
  const extractSimpleBulletPoints = (content: string): string[] => {
    if (!content) return [];
    
    console.log("=== SIMPLE BULLET EXTRACTION DEBUG ===");
    console.log("Content for simple extraction:", content);
    
    const lines = content.split('\n');
    const bulletPoints: string[] = [];
    
    console.log("Total lines in simple extraction:", lines.length);
    
    // If content is all on one line, try to split by bullet symbols
    if (lines.length === 1 && lines[0].length > 100) {
      console.log("Content appears to be on one line, trying bullet symbol splitting...");
      
      // Try to split by bullet symbols that might be embedded in the text
      const bulletSymbols = ['•', '-', '*', '○', '▪', '▫'];
      
      bulletSymbols.forEach(symbol => {
        if (content.includes(symbol)) {
          console.log(`Found bullet symbol "${symbol}" in content`);
          const parts = content.split(symbol);
          console.log(`Split by "${symbol}" into ${parts.length} parts`);
          
          parts.forEach((part, index) => {
            if (index > 0) { // Skip first part (before first bullet)
              const trimmedPart = part.trim();
              if (trimmedPart.length > 10 && trimmedPart.length < 200) {
                bulletPoints.push(trimmedPart);
                console.log(`Found bullet from symbol split: "${trimmedPart}"`);
              }
            }
          });
        }
      });
    }
    
    // Also try line-by-line extraction
    lines.forEach((line, index) => {
      const trimmedLine = line.trim();
      console.log(`Simple extraction line ${index}: "${trimmedLine}"`);
      
      // Check for various bullet symbols
      if (trimmedLine && (
        trimmedLine.startsWith('•') ||
        trimmedLine.startsWith('-') ||
        trimmedLine.startsWith('*') ||
        trimmedLine.startsWith('○') ||
        trimmedLine.startsWith('▪') ||
        trimmedLine.startsWith('▫')
      )) {
        const cleanBullet = trimmedLine.replace(/^[•\-*○▪▫]\s*/, '').trim();
        if (cleanBullet.length > 0) {
          bulletPoints.push(cleanBullet);
          console.log(`Simple extraction FOUND bullet: "${cleanBullet}"`);
        }
      }
    });
    
    console.log("Simple extraction found bullets:", bulletPoints);
    console.log("=== END SIMPLE EXTRACTION DEBUG ===");
    
    return bulletPoints;
  };
  

  const bulletPoints = extractBulletPoints(resumeContent);
  const simpleBulletPoints = extractSimpleBulletPoints(resumeContent);
  
  // Use simple extraction if main extraction fails
  const finalBulletPoints = bulletPoints.length > 0 ? bulletPoints : simpleBulletPoints;
  
  // Simple post-processing to clean up bullets
  const cleanBulletPoints = (bullets: string[]): string[] => {
    return bullets.filter(bullet => {
      // Keep bullets that are reasonable length and contain letters
      return bullet.length > 10 && bullet.length < 500 && bullet.match(/[a-zA-Z]/);
    });
  };
  
  const cleanedBulletPoints = cleanBulletPoints(finalBulletPoints);

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
        {cleanedBulletPoints.length > 0 ? (
          cleanedBulletPoints.map((bullet, index) => (
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
            <p>Main extraction found: {bulletPoints.length} bullet points</p>
            <p>Simple extraction found: {simpleBulletPoints.length} bullet points</p>
            <p>Final cleaned bullets: {cleanedBulletPoints.length} bullet points</p>
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