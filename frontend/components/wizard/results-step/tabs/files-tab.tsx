"use client"

import * as React from "react"
import { DetailedResults } from "../../types"

interface FilesTabProps {
    results: DetailedResults
}

export function FilesTab({ results }: FilesTabProps) {
    const mainFile = results.file
    const supportingFiles = results.supporting_files || []

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-lg font-semibold">Main File</h3>
                <div className="mt-3 border rounded-lg p-4">
                    <div className="text-sm">
                        <p><strong>Name:</strong> {mainFile?.name || 'Unknown'}</p>
                        {typeof mainFile?.size === 'number' && (
                            <p className="text-muted-foreground">Size: {Math.round(mainFile.size / 1024)} KB</p>
                        )}
                        {typeof (mainFile as any)?.type === 'string' && (
                            <p className="text-muted-foreground">Type: {(mainFile as any).type}</p>
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
                                        <p><strong>Name:</strong> {file.name}</p>
                                        {typeof file.size === 'number' && (
                                            <p className="text-muted-foreground">Size: {Math.round(file.size / 1024)} KB</p>
                                        )}
                                        {typeof (file as any)?.type === 'string' && (
                                            <p className="text-muted-foreground">Type: {(file as any).type}</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}


