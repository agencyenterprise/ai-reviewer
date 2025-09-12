"use client"

import * as React from "react"
import { DetailedResults } from "../../types"
import { ChunkDisplay, ChunkItem } from "../components/chunk-display"
import { AlertTriangle, FileIcon, Link as LinkIcon } from "lucide-react"

interface ChunksTabProps {
    results: DetailedResults
}

export function ChunksTab({ results }: ChunksTabProps) {
    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold">Chunks</h3>
            <div className="space-y-4">
                {results.claims_by_chunk.map((claimsChunk, chunkIndex) => {
                    const chunk = results.chunks[chunkIndex]
                    const claims = claimsChunk?.claims || []
                    const references = results.references || []
                    const supportingFiles = results.supporting_files || []
                    const citationsChunk = results.citations_by_chunk[chunkIndex]
                    const citations = citationsChunk?.citations || []
                    const chunkText = chunk?.page_content || 'No content provided.'
                    const hasUnsubstantiated = (results.claim_substantiations_by_chunk[chunkIndex] || [])
                        .some(s => !s.is_substantiated)
                    const substantiatedClaims = results.claim_substantiations_by_chunk[chunkIndex].filter(s => s.is_substantiated) || []
                    const substantiatedClaimIndices = substantiatedClaims.map(s => s.claim_index)
                    const unsubstantiatedClaims = results.claim_substantiations_by_chunk[chunkIndex].filter(s => !s.is_substantiated) || []
                    const unsubstantiatedClaimIndices = unsubstantiatedClaims.map(s => s.claim_index)

                    return (
                        <div
                            key={chunkIndex}
                            className={`border rounded-lg ${hasUnsubstantiated ? 'border-red-200 bg-red-50/40' : ''}`}
                       >
                            <div className={`flex items-center justify-between px-4 py-2 border-b ${hasUnsubstantiated ? 'bg-red-50' : 'bg-muted/50'}`}>
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
                                <h4 className="text-sm font-medium mb-2">Text</h4>
                                <ChunkItem>
                                    <p className="text-sm whitespace-pre-wrap">{chunkText}</p>
                                </ChunkItem>

                                {claims.length > 0 && (
                                    <div>
                                        <h4 className="text-sm font-medium mb-2">Claims</h4>
                                        <div className="space-y-2">
                                            {claims.map((claim, ci) => (
                                                <ChunkItem key={ci} className={unsubstantiatedClaimIndices.includes(ci) ? 'bg-red-50/40' : ''}>
                                                    <p className="text-sm"><strong>Claim:</strong> {claim.claim}</p>
                                                    <p className="text-sm text-muted-foreground mt-1"><strong>Related Text:</strong> "{claim.text}"</p>
                                                    {substantiatedClaimIndices.includes(ci) && (
                                                        <p className="text-sm text-green-600 mt-1">
                                                            <strong>Substantiated because:</strong> {substantiatedClaims[substantiatedClaimIndices.find(i => i == ci)!].rationale}
                                                        </p>
                                                    )}
                                                    {unsubstantiatedClaimIndices.includes(ci) && (
                                                        <>  
                                                            <p className="text-sm text-red-600 mt-1">
                                                                <strong>Unsubstantiated because:</strong> {unsubstantiatedClaims[unsubstantiatedClaimIndices.find(i => i == ci)!].rationale}
                                                            </p>
                                                            <p className="text-sm text-blue-600 mt-1">
                                                                <strong>Feedback to resolve:</strong> {unsubstantiatedClaims[unsubstantiatedClaimIndices.find(i => i == ci)!].feedback}
                                                            </p>
                                                        </>
                                                    )}
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
                                                    {citation.associated_bibliography && (
                                                        <div className="text-xs text-muted-foreground mt-1">
                                                            <strong>Associated bibliography:</strong> {citation.associated_bibliography}
                                                            {citation.index_of_associated_bibliography && references[citation.index_of_associated_bibliography - 1]?.has_associated_supporting_document && (
                                                                <div className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                                                                    <strong>Related supporting document:</strong>
                                                                    <FileIcon className="w-3 h-3" />
                                                                    {supportingFiles[references[citation.index_of_associated_bibliography - 1]?.index_of_associated_supporting_document - 1]?.file_name}
                                                                </div>
                                                            )}
                                                            {citation.index_of_associated_bibliography && references[citation.index_of_associated_bibliography - 1] && !references[citation.index_of_associated_bibliography - 1].has_associated_supporting_document && (
                                                                <div className="text-xs text-muted-foreground mt-1">
                                                                    <strong>No related supporting document:</strong>
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
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


