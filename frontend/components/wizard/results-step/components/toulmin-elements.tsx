import { Badge } from '@/components/ui/badge';
import { Quote, Shield, Scale, RotateCcw, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';

export const ToulminElement = {
  DATA: { icon: Quote, color: 'blue', label: 'Data/Grounds' },
  WARRANT: { icon: Shield, color: 'purple', label: 'Warrants' },
  QUALIFIER: { icon: Scale, color: 'green', label: 'Qualifiers' },
  REBUTTAL: { icon: RotateCcw, color: 'orange', label: 'Rebuttals' },
  BACKING: { icon: Layers, color: 'indigo', label: 'Backing' },
} as const;

export type ToulminElementType = (typeof ToulminElement)[keyof typeof ToulminElement];

export interface ToulminElementCardProps {
  element: ToulminElementType;
  items?: string[];
  warrantExpression?: string;
}

export function ToulminElementCard({ element, items, warrantExpression }: ToulminElementCardProps) {
  const Icon = element.icon;

  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div
          className={cn(
            'p-1.5 rounded-full',
            element.color === 'blue' && 'bg-blue-100',
            element.color === 'purple' && 'bg-purple-100',
            element.color === 'green' && 'bg-green-100',
            element.color === 'orange' && 'bg-orange-100',
            element.color === 'indigo' && 'bg-indigo-100',
          )}
        >
          <Icon
            className={cn(
              'h-4 w-4',
              element.color === 'blue' && 'text-blue-600',
              element.color === 'purple' && 'text-purple-600',
              element.color === 'green' && 'text-green-600',
              element.color === 'orange' && 'text-orange-600',
              element.color === 'indigo' && 'text-indigo-600',
            )}
          />
        </div>
        <h4 className="font-medium text-gray-900">{element.label}</h4>
        {warrantExpression && (
          <Badge
            variant="outline"
            className={cn('text-xs', element.color === 'purple' && 'bg-purple-50 text-purple-700 border-purple-200')}
          >
            {warrantExpression}
          </Badge>
        )}
      </div>

      <div className="space-y-2">
        {items.map((item, index) => (
          <div
            key={index}
            className={cn(
              'p-3 rounded-md text-sm',
              element.color === 'blue' && 'bg-blue-50 border-l-4 border-blue-400',
              element.color === 'purple' && 'bg-purple-50 border-l-4 border-purple-400',
              element.color === 'green' && 'bg-green-50 border-l-4 border-green-400',
              element.color === 'orange' && 'bg-orange-50 border-l-4 border-orange-400',
              element.color === 'indigo' && 'bg-indigo-50 border-l-4 border-indigo-400',
            )}
          >
            <p className="text-gray-700 leading-relaxed">{item}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
