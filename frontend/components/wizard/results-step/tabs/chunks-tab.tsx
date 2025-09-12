"use client"

import * as React from "react"
import { DetailedResults } from "../../types"
import { ChunkDisplay, ChunkItem } from "../components/chunk-display"
import { AlertTriangle, Link as LinkIcon } from "lucide-react"

interface ChunksTabProps {
    results: DetailedResults
}

export function ChunksTab({ results }: ChunksTabProps) {
    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold">Chunks</h3>
            <div className="space-y-4 max-h-96 overflow-y-auto">
                {results.claims_by_chunk.map((claimsChunk, chunkIndex) => {
                    const claims = claimsChunk?.claims || []
                    const citationsChunk = results.citations_by_chunk[chunkIndex]
                    const citations = citationsChunk?.citations || []
                    const chunkText = claimsChunk?.rationale || citationsChunk?.rationale || 'No content provided.'
                    const hasUnsubstantiated = (results.claim_substantiations_by_chunk[chunkIndex] || [])
                        .some(s => !s.is_substantiated)

                    return (
                        <div key={chunkIndex} className="border rounded-lg">
                            <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/50">
                                <div className="flex items-center gap-2">
                                    <span className="font-medium">Chunk {chunkIndex + 1}</span>
                                    {hasUnsubstantiated && (
                                        <span title="Unsubstantiated claims present" className="inline-flex items-center gap-1 text-red-600 text-xs">
                                            <AlertTriangle className="w-3 h-3" />
                                            Unsubstantiated
                                        </span>
                                    )}
                                </div>
                                {citations.length > 0 && (
                                    <span className="inline-flex items-center gap-1 text-blue-600 text-xs">
                                        <LinkIcon className="w-3 h-3" />
                                        {citations.length} citation{citations.length > 1 ? 's' : ''}
                                    </span>
                                )}
                            </div>

                            <div className="p-4 space-y-4">
                                <ChunkItem>
                                    <p className="text-sm whitespace-pre-wrap">{chunkText}</p>
                                </ChunkItem>

                                {claims.length > 0 && (
                                    <div>
                                        <h4 className="text-sm font-medium mb-2">Claims</h4>
                                        <div className="space-y-2">
                                            {claims.map((claim, ci) => (
                                                <ChunkItem key={ci}>
                                                    <p className="text-sm"><strong>Claim:</strong> {claim.claim}</p>
                                                    <p className="text-xs text-muted-foreground mt-1"><strong>Text:</strong> "{claim.text}"</p>
                                                </ChunkItem>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {citations.length > 0 && (
                                    <div>
                                        <h4 className="text-sm font-medium mb-2">Citations</h4>
                                        <div className="space-y-2">
                                            {citations.map((citation, ci) => (
                                                <ChunkItem key={ci}>
                                                    <p className="text-sm"><strong>Citation:</strong> {citation.text}</p>
                                                    <div className="flex gap-2 text-xs mt-1">
                                                        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">{citation.type}</span>
                                                        <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">{citation.format}</span>
                                                    </div>
                                                </ChunkItem>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}


