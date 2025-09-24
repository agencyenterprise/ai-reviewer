'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Progress } from '../ui/progress';
import { useWizard } from './wizard-context';
import { Loader2 } from 'lucide-react';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

export function ProcessStep() {
  const { state, actions } = useWizard();

  if (state.isProcessing) {
    return (
      <div className="space-y-6">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 mx-auto animate-spin text-primary" />
          <h2 className="text-2xl font-bold">Processing Documents</h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            AI is analyzing your documents for claims, citations, and accuracy...
          </p>
        </div>
        <Card className="max-w-xl mx-auto">
          <CardContent className="py-8">
            <div className="space-y-4">
              <Progress value={65} className="w-full" />
              <p className="text-sm text-center text-muted-foreground">Detecting claims and verifying citations...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="max-w-xl mx-auto">
        <CardHeader>
          <CardTitle>Document Summary</CardTitle>
          <CardDescription>Documents ready for processing</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span>Main Document:</span>
              <span className="font-medium">{state.mainDocument?.name}</span>
            </div>
            <div className="flex justify-between">
              <span>Supporting Documents:</span>
              <span className="font-medium">{state.supportingDocuments.length}</span>
            </div>
            <div className="flex justify-between">
              <span>Analysis Type:</span>
              <span className="font-medium">Claims & Citations</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="max-w-xl mx-auto">
        <CardHeader>
          <CardTitle>Analysis Configuration</CardTitle>
          <CardDescription>Provide context for more accurate analysis</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="domain">Domain</Label>
            <Input
              id="domain"
              placeholder="e.g., Healthcare, Technology, Finance..."
              value={state.domain}
              onChange={(e) => actions.setDomain(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="target-audience">Target Audience</Label>
            <Input
              id="target-audience"
              placeholder="e.g., General public, Experts, Students..."
              value={state.targetAudience}
              onChange={(e) => actions.setTargetAudience(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <p className="text-muted-foreground max-w-md mx-auto text-center">
        Ready to analyze your documents for claims, citations, and accuracy
      </p>
    </div>
  );
}
