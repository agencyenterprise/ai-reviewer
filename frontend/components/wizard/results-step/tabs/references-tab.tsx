"use client"

import * as React from "react"
import { DetailedResults } from "../../types"

interface ReferencesTabProps {
    results: DetailedResults
}

export function ReferencesTab({ results }: ReferencesTabProps) {
    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold">References</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
                {results.references.map((reference, index) => (
                    <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                            <p className="text-sm flex-1">{reference.text}</p>
                            <div className={`ml-3 px-2 py-1 rounded text-xs ${reference.has_associated_supporting_document
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-orange-100 text-orange-800'
                                }`}>
                                {reference.has_associated_supporting_document ? 'Supported' : 'No Support'}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
