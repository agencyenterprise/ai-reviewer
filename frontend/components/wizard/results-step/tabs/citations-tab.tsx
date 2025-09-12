"use client"

import * as React from "react"
import { DetailedResults } from "../../types"
import { ChunkDisplay, ChunkItem } from "../components/chunk-display"

interface CitationsTabProps {
    results: DetailedResults
}

export function CitationsTab({ results }: CitationsTabProps) {
    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold">Citations Analysis</h3>
            <div className="space-y-4">
                {results.citations_by_chunk.map((chunk, chunkIndex) =>
                    chunk.citations.length > 0 && (
                        <ChunkDisplay key={chunkIndex} chunkIndex={chunkIndex}>
                            {chunk.citations.map((citation, citationIndex) => (
                                <ChunkItem key={citationIndex}>
                                    <p className="text-sm mb-2">
                                        <strong>Citation:</strong> {citation.text}
                                    </p>
                                    <div className="flex gap-2 text-xs">
                                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                            {citation.type}
                                        </span>
                                        <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">
                                            {citation.format}
                                        </span>
                                    </div>
                                    {citation.associated_bibliography && (
                                        <p className="text-xs text-muted-foreground mt-2">
                                            <strong>Bibliography:</strong> {citation.associated_bibliography}
                                        </p>
                                    )}
                                </ChunkItem>
                            ))}
                        </ChunkDisplay>
                    )
                )}
            </div>
        </div>
    )
}
