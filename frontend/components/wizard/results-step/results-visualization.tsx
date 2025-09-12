"use client"

import * as React from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../ui/card"
import { AnalysisResults, DetailedResults } from "../types"
import { useResultsCalculations } from "./hooks/use-results-calculations"
import { SummaryCards, TabNavigation } from "./components"
import { SummaryTab, ClaimsTab, CitationsTab, ReferencesTab, FilesTab } from "./tabs"
import { TabType } from "./constants"

interface ResultsVisualizationProps {
    results: AnalysisResults | null
}

export function ResultsVisualization({ results }: ResultsVisualizationProps) {
    const detailedResults = results?.fullResults as DetailedResults | undefined
    const [activeTab, setActiveTab] = React.useState<TabType>('summary')

    const calculations = useResultsCalculations(detailedResults)

    if (!results || !detailedResults) {
        return (
            <Card className="max-w-4xl mx-auto">
                <CardHeader>
                    <CardTitle>No Results Available</CardTitle>
                    <CardDescription>
                        No analysis results to display
                    </CardDescription>
                </CardHeader>
            </Card>
        )
    }

    const renderActiveTab = () => {
        switch (activeTab) {
            case 'summary':
                return (
                    <SummaryTab
                        results={detailedResults}
                        chunksWithClaims={calculations.chunksWithClaims}
                        chunksWithCitations={calculations.chunksWithCitations}
                        supportedReferences={calculations.supportedReferences}
                    />
                )
            case 'claims':
                return <ClaimsTab results={detailedResults} />
            case 'citations':
                return <CitationsTab results={detailedResults} />
            case 'references':
                return <ReferencesTab results={detailedResults} />
            case 'files':
                return <FilesTab results={detailedResults} />
        }
    }

    return (
        <div className="space-y-6 max-w-6xl mx-auto">
            <SummaryCards
                totalClaims={calculations.totalClaims}
                totalCitations={calculations.totalCitations}
                totalUnsubstantiated={calculations.totalUnsubstantiated}
            />

            <TabNavigation
                activeTab={activeTab}
                onTabChange={setActiveTab}
            />

            <Card>
                <CardContent className="p-6">
                    {renderActiveTab()}
                </CardContent>
            </Card>
        </div>
    )
}
