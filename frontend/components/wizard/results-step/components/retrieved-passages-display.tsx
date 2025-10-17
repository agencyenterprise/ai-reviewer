import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import type { RetrievedPassageInfo } from '@/lib/generated-api';

interface RetrievedPassagesDisplayProps {
  passages: RetrievedPassageInfo[];
}

export function RetrievedPassagesDisplay({ passages }: RetrievedPassagesDisplayProps) {
  if (!passages || passages.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 text-sm">
      <Accordion type="single" collapsible>
        <AccordionItem value="retrieved-passages">
          <AccordionTrigger className="text-sm font-medium">
            📚 Retrieved Evidence ({passages.length} passages)
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-3 mt-2">
              {passages.map((passage, idx) => (
                <div key={idx} className="border-l-2 border-gray-200 pl-3 py-2">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-medium text-gray-700">{passage.sourceFile}</span>
                    <Badge variant="outline" className="text-xs">
                      {(passage.similarityScore * 100).toFixed(0)}% match
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600 line-clamp-3">{passage.content}</p>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  );
}
