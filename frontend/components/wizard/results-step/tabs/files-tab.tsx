'use client';

import { ClaimSubstantiatorState } from '@/lib/generated-api';
import * as React from 'react';

interface FilesTabProps {
  results: ClaimSubstantiatorState;
}

export function FilesTab({ results }: FilesTabProps) {
  const mainFile = results.file;
  const supportingFiles = results.supportingFiles || [];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Main File</h3>
        <div className="mt-3 border rounded-lg p-4">
          <div className="text-sm">
            <p>
              <strong>Name:</strong> {mainFile?.fileName || 'Unknown'}
            </p>
            {typeof mainFile?.fileType === 'string' && (
              <p className="text-muted-foreground">Type: {mainFile.fileType}</p>
            )}
            {typeof mainFile?.filePath === 'string' && (
              <p className="text-muted-foreground break-all">Path: {mainFile.filePath}</p>
            )}
            {typeof mainFile?.markdown === 'string' && (
              <div className="mt-3">
                <p className="text-sm text-muted-foreground mb-1">Content</p>
                <div className="text-xs whitespace-pre-wrap border rounded-md p-3 max-h-64 overflow-auto bg-muted/30">
                  {mainFile.markdown}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold">Supporting Files</h3>
        {supportingFiles.length === 0 ? (
          <p className="text-sm text-muted-foreground mt-2">No supporting files uploaded.</p>
        ) : (
          <div className="mt-3 space-y-3 max-h-96 overflow-y-auto">
            {supportingFiles.map((file, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-start justify-between w-full">
                  <div className="text-sm">
                    <p>
                      <strong>Name:</strong> {file.fileName}
                    </p>
                    {typeof file.fileType === 'string' && (
                      <p className="text-muted-foreground">Type: {file.fileType}</p>
                    )}
                    {typeof file.filePath === 'string' && (
                      <p className="text-muted-foreground break-all">Path: {file.filePath}</p>
                    )}
                    {typeof file.markdown === 'string' && (
                      <div className="mt-3">
                        <p className="text-sm text-muted-foreground mb-1">Content</p>
                        <div className="text-xs whitespace-pre-wrap border rounded-md p-3 max-h-64 overflow-auto bg-muted/30">
                          {file.markdown}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
