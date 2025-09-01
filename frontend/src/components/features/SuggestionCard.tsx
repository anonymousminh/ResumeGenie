'use client';

import { useState } from 'react';

interface SuggestionCardProps {
  selectedBullet: string;
  jobPostingContent: string;
  rewrittenBullet: string;
  isLoading: boolean;
}

export default function SuggestionCard({ 
  selectedBullet, 
  jobPostingContent, 
  rewrittenBullet, 
  isLoading 
}: SuggestionCardProps) {
  if (!selectedBullet) {
    return (
      <div className="p-4 border rounded-lg">
        <h3 className="font-bold">Bullet Point Rewriting</h3>
        <p className="text-gray-500">Select a bullet point from your resume to get rewriting suggestions.</p>
      </div>
    );
  }

  return (
    <div className="p-4 border rounded-lg">
      <h3 className="font-bold mb-4">Rewritten Bullet Point</h3>
      
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Rewriting bullet point...</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Original Bullet Point */}
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Original:</h4>
            <div className="p-3 bg-gray-50 border rounded-md">
              <p className="text-sm text-gray-800">{selectedBullet}</p>
            </div>
          </div>

          {/* Rewritten Bullet Point */}
          {rewrittenBullet && (
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Rewritten:</h4>
              <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                <p className="text-sm text-green-800">{rewrittenBullet}</p>
              </div>
            </div>
          )}

          {/* Copy Button */}
          {rewrittenBullet && (
            <button
              onClick={() => {
                navigator.clipboard.writeText(rewrittenBullet);
                // You could add a toast notification here
              }}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition-colors"
            >
              Copy Rewritten Bullet
            </button>
          )}
        </div>
      )}
    </div>
  );
}