'use client';

import * as React from 'react';
import { DetailedResults } from '../../types';

interface FilesTabProps {
  results: DetailedResults;
}

export function FilesTab({ results }: FilesTabProps) {
  const mainFile = results.file;
  const supportingFiles = results.supporting_files || [];

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">Main File</h3>
        <div className="mt-3 border rounded-lg p-4">
          <div className="text-sm">
            <p>
              <strong>Name:</strong> {mainFile?.file_name || 'Unknown'}
            </p>
            {typeof mainFile?.file_type === 'string' && (
              <p className="text-muted-foreground">Type: {mainFile.file_type}</p>
            )}
            {typeof mainFile?.file_path === 'string' && (
              <p className="text-muted-foreground break-all">Path: {mainFile.file_path}</p>
            )}
            {typeof mainFile?._markdown === 'string' && (
              <div className="mt-3">
                <p className="text-sm text-muted-foreground mb-1">Content</p>
                <div className="text-xs whitespace-pre-wrap border rounded-md p-3 max-h-64 overflow-auto bg-muted/30">
                  {mainFile._markdown}
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
                      <strong>Name:</strong> {file.file_name}
                    </p>
                    {typeof file.file_type === 'string' && (
                      <p className="text-muted-foreground">Type: {file.file_type}</p>
                    )}
                    {typeof file.file_path === 'string' && (
                      <p className="text-muted-foreground break-all">Path: {file.file_path}</p>
                    )}
                    {typeof file._markdown === 'string' && (
                      <div className="mt-3">
                        <p className="text-sm text-muted-foreground mb-1">Content</p>
                        <div className="text-xs whitespace-pre-wrap border rounded-md p-3 max-h-64 overflow-auto bg-muted/30">
                          {file._markdown}
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
