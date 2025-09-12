'use client';

import { useWizard } from '../wizard-context';
import { UploadSection } from './upload-section';

export function UploadStep() {
  const { state, actions } = useWizard();

  const removeFile = (type: 'main' | 'supporting', index?: number) => {
    if (type === 'main') {
      actions.setMainDocument(null);
    } else if (typeof index === 'number') {
      const newFiles = state.supportingDocuments.filter((_, i) => i !== index);
      actions.setSupportingDocuments(newFiles);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        <UploadSection
          title="Main Document"
          description="Primary document for analysis"
          badgeText="Required"
          badgeClass="bg-primary/10 text-primary border border-primary/20"
          onFilesChange={(files) => actions.setMainDocument(files[0] || null)}
          multiple={false}
          files={state.mainDocument ? [state.mainDocument] : []}
          fileType="main"
          onRemoveFile={() => removeFile('main')}
        />

        <UploadSection
          title="Supporting Documents"
          description="Additional references and context"
          badgeText="Optional"
          badgeClass="bg-muted/60 text-muted-foreground border border-muted"
          onFilesChange={actions.setSupportingDocuments}
          multiple={true}
          files={state.supportingDocuments}
          fileType="supporting"
          onRemoveFile={(index) => removeFile('supporting', index)}
        />
      </div>

      <div className="text-center mb-12">
        <p className="text-muted-foreground max-w-md mx-auto">
          Upload your main document and supporting references for AI analysis
        </p>
      </div>
    </div>
  );
}
