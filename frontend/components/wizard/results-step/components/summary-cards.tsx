"use client"

import * as React from "react"
import { FileText, BookOpen, AlertTriangle } from "lucide-react"
import { Card, CardContent } from "../../../ui/card"

interface SummaryCardsProps {
    totalClaims: number
    totalCitations: number
    totalUnsubstantiated: number
}

export function SummaryCards({ totalClaims, totalCitations, totalUnsubstantiated }: SummaryCardsProps) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center space-x-2">
                        <FileText className="h-8 w-8 text-blue-500" />
                        <div>
                            <div className="text-2xl font-bold">{totalClaims}</div>
                            <p className="text-xs text-muted-foreground">Claims Detected</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center space-x-2">
                        <BookOpen className="h-8 w-8 text-green-500" />
                        <div>
                            <div className="text-2xl font-bold">{totalCitations}</div>
                            <p className="text-xs text-muted-foreground">Citations Found</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center space-x-2">
                        <AlertTriangle className="h-8 w-8 text-orange-500" />
                        <div>
                            <div className="text-2xl font-bold">{totalUnsubstantiated}</div>
                            <p className="text-xs text-muted-foreground">Unsubstantiated</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
