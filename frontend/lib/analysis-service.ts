import { AnalysisResults, DetailedResults } from "@/components/wizard/types"

interface AnalysisRequest {
    mainDocument: File
    supportingDocuments?: File[]
}

interface ApiResponse {
    claims?: Array<{ is_substantiated: boolean }>
    citations?: Array<any>
    [key: string]: any
}

class AnalysisService {
    private readonly apiUrl: string

    constructor() {
        this.apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    }

    private prepareFormData({ mainDocument, supportingDocuments = [] }: AnalysisRequest): FormData {
        const formData = new FormData()
        formData.append('main_document', mainDocument)

        supportingDocuments.forEach((doc) => {
            formData.append('supporting_documents', doc)
        })

        return formData
    }

    private transformResponse(apiResponse: ApiResponse): AnalysisResults {
        return {
            claimsDetected: apiResponse.claims?.length || 0,
            citationsFound: apiResponse.citations?.length || 0,
            unsubstantiatedClaims:
                apiResponse.claims?.filter((claim) => !claim.is_substantiated)?.length || 0,
            status: "completed",
            fullResults: apiResponse as DetailedResults
        }
    }

    private createErrorResult(error: unknown): AnalysisResults {
        const errorMessage = error instanceof Error
            ? error.message
            : 'Unknown error occurred'

        return {
            claimsDetected: 0,
            citationsFound: 0,
            unsubstantiatedClaims: 0,
            status: "error",
            error: errorMessage
        }
    }

    async runClaimSubstantiation(request: AnalysisRequest): Promise<AnalysisResults> {
        try {
            const formData = this.prepareFormData(request)

            const response = await fetch(`${this.apiUrl}/api/run-claim-substantiation`, {
                method: 'POST',
                body: formData,
            })

            if (!response.ok) {
                throw new Error(`API call failed: ${response.status} ${response.statusText}`)
            }

            const result = await response.json()
            return this.transformResponse(result)

        } catch (error) {
            console.error('Error calling claim substantiation API:', error)
            return this.createErrorResult(error)
        }
    }
}

export const analysisService = new AnalysisService()

export { AnalysisService }
export type { AnalysisRequest }
