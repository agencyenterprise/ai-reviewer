"use client"

import * as React from "react"

interface ChunkDisplayProps {
    chunkIndex: number
    children: React.ReactNode
}

export function ChunkDisplay({ chunkIndex, children }: ChunkDisplayProps) {
    return (
        <div className="border rounded-lg p-4">
            <h4 className="font-medium mb-2">Chunk {chunkIndex + 1}</h4>
            {children}
        </div>
    )
}

interface ChunkItemProps {
    children: React.ReactNode
    className?: string
}

export function ChunkItem({ children, className = "" }: ChunkItemProps) {
    return (
        <div className={`mb-3 p-3 bg-muted rounded ${className}`}>
            {children}
        </div>
    )
}
