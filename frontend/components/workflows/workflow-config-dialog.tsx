import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { HelpLink } from '@/components/help/help-link';
import { HelpTopicId } from '@/components/help/topics';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useExperimentalFeatures } from '@/context/experimental-features-context';
import { GlobalFormValidationError, useForm } from '@tanstack/react-form';
import { useWorkflowTypes } from '@/lib/hooks/use-workflow-types';
import { useUserMe } from '@/lib/hooks/use-user-me';
import { WorkflowRunType } from '@/lib/generated-api';
import { KeyRound } from 'lucide-react';
import { useEffect } from 'react';
import { WorkflowTypeSelector } from './workflow-type-selector';
import { WebSearchConsentCheckbox } from './web-search-consent-checkbox';
import { hasWebSearchRequirement, hasPublicationDateRequirement } from './utils';
import { useWebSearchConsent } from '@/lib/hooks/use-web-search-consent';

interface WorkflowConfigDialogProps {
  isOpen: boolean;
  type?: WorkflowRunType;
  projectId: string;
  onConfirm: (values: WorkflowConfigFormValues) => void;
  onCancel: () => void;
  /**
   * Names the action in the caller's own words. Without these the dialog talks
   * about running an assessment, which is wrong for the internal workflows —
   * nobody asked to "run Reference Downloader", they asked to fetch a source.
   */
  title?: string;
  description?: string;
  submitLabel?: string;
  /** The help topic the dialog's link opens. Follows what the dialog is for. */
  helpTopic?: HelpTopicId;
}

export interface WorkflowConfigFormValues {
  webSearchConsent: boolean;
  publicationDate: string;
  workflowTypes: WorkflowRunType[];
}

export function WorkflowConfigDialog({
  isOpen,
  type,
  projectId,
  onConfirm,
  onCancel,
  title,
  description,
  submitLabel,
  helpTopic = 'assessments',
}: WorkflowConfigDialogProps) {
  const [storedWebSearchConsent] = useWebSearchConsent(projectId);
  const { showExperimentalFeatures } = useExperimentalFeatures();
  const { data: user } = useUserMe();

  const { workflowTypes, getWorkflowTypeName } = useWorkflowTypes();

  // Named when the dialog is opened for one assessment; otherwise it is the
  // picker over all of them.
  const assessmentName = type ? getWorkflowTypeName(type) : null;

  const needsPublicationDate = type ? hasPublicationDateRequirement([type]) : false;

  // WHY: Default to today's date so when experimental features are disabled,
  // the form still submits a valid date without showing the field to the user.
  const today = new Date().toISOString().split('T')[0];

  // WHY: Only show publication date field when the user has opted into experimental features.
  // When disabled, we simplify the UI by hiding this field and using today's date.
  const showPublicationDateField = showExperimentalFeatures && needsPublicationDate;

  const form = useForm({
    defaultValues: {
      webSearchConsent: storedWebSearchConsent,
      publicationDate: today,
      workflowTypes: type ? [type] : [],
    } as WorkflowConfigFormValues,
    validators: {
      onChange: ({ value }) => {
        const errors: GlobalFormValidationError<WorkflowConfigFormValues> = { fields: {}, form: undefined };
        if (hasWebSearchRequirement(value.workflowTypes, workflowTypes) && !value.webSearchConsent) {
          errors.fields.webSearchConsent = 'Web search consent is required';
        }
        // Only require publication date input when the field is shown
        if (showPublicationDateField && (!value.publicationDate || value.publicationDate.trim() === '')) {
          errors.fields.publicationDate = 'Document publication date is required';
        }
        if (value.workflowTypes.length === 0) {
          errors.fields.workflowTypes = 'At least one workflow type must be selected';
        }
        return errors;
      },
    },
    onSubmit: ({ value }) => {
      onConfirm(value);
    },
  });

  useEffect(() => {
    if (isOpen) {
      // Reset the form every time the dialog is opened
      form.reset();
    }
  }, [form, isOpen]);

  return (
    <Dialog open={isOpen} onOpenChange={onCancel}>
      {/* Wide enough for the two-column assessment grid this dialog renders when
          no specific `type` is given. */}
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title ?? (assessmentName ? `Run ${assessmentName}` : 'Run assessments')}</DialogTitle>
          <DialogDescription>
            {description ??
              (assessmentName
                ? 'Confirm how this assessment should run on your document.'
                : 'Choose which assessments to run on your document.')}{' '}
            <HelpLink topic={helpTopic}>
              {helpTopic === 'assessments' ? 'How assessments work' : 'What this is for'}
            </HelpLink>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {showPublicationDateField && (
            <form.Field name="publicationDate">
              {(field) => (
                <div className="space-y-2">
                  <Label htmlFor="publication-date" required>
                    Document Publication Date
                  </Label>
                  <Input
                    id="publication-date"
                    type="date"
                    value={field.state.value}
                    onChange={(e) => field.handleChange(e.target.value)}
                    error={!field.state.meta.isValid}
                    required={true}
                  />
                  <p className="text-sm text-muted-foreground">
                    The publication date of the document. For unpublished documents, use the date of the last update or
                    the current date.
                  </p>
                  {!field.state.meta.isValid && (
                    <p className="text-sm text-destructive">{field.state.meta.errors.join(', ')}</p>
                  )}
                </div>
              )}
            </form.Field>
          )}

          <form.Field name="workflowTypes">
            {(field) => (
              <WorkflowTypeSelector
                restrictToType={type}
                projectId={projectId}
                selectedTypes={field.state.value}
                onSelectionChange={field.handleChange}
                disabledTypes={type ? [type] : undefined}
                error={
                  !field.state.meta.isValid && field.state.meta.errors.length > 0
                    ? field.state.meta.errors.join(', ')
                    : undefined
                }
              />
            )}
          </form.Field>

          <form.Field name="workflowTypes">
            {(workflowTypesField) => {
              const selectedTypes = workflowTypesField.state.value;
              const needsWebSearch = hasWebSearchRequirement(selectedTypes, workflowTypes);

              if (!needsWebSearch) {
                return null;
              }

              return (
                <form.Field name="webSearchConsent">
                  {(field) => (
                    <WebSearchConsentCheckbox
                      checked={field.state.value}
                      onCheckedChange={field.handleChange}
                      error={!field.state.meta.isValid ? field.state.meta.errors.join(', ') : undefined}
                    />
                  )}
                </form.Field>
              );
            }}
          </form.Field>
        </div>

        {user?.has_openai_api_key && (
          <p className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <KeyRound className="h-3.5 w-3.5 shrink-0" />
            Your saved OpenAI API key will be used for this assessment.
          </p>
        )}

        <form.Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
          {([canSubmit, isSubmitting]) => (
            <DialogFooter>
              <Button variant="outline" onClick={onCancel} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button onClick={() => form.handleSubmit()} disabled={!canSubmit || isSubmitting}>
                {isSubmitting
                  ? 'Starting...'
                  : (submitLabel ?? (assessmentName ? 'Run assessment' : 'Run assessments'))}
              </Button>
            </DialogFooter>
          )}
        </form.Subscribe>
      </DialogContent>
    </Dialog>
  );
}
