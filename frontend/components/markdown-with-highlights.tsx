import { cn } from '@/lib/utils';
import { ComponentType, JSX } from 'react';
import ReactMarkdown, { ExtraProps } from 'react-markdown';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { HighlightWord } from '@/lib/generated-api';

type MarkdownComponentProps<Key extends keyof JSX.IntrinsicElements> = JSX.IntrinsicElements[Key] & ExtraProps;

interface MarkdownWithHighlightsProps extends React.ComponentProps<typeof ReactMarkdown> {
  highlightWords?: HighlightWord[];
  baseHighlight?: 'red' | 'yellow' | 'blue' | 'green' | 'none';
}

const highlightText = (text: string, words: HighlightWord[]): JSX.Element[] => {
  if (!words || words.length === 0) {
    return [<span key="0">{text}</span>];
  }

  // Debug: Log highlighting attempt (remove in production)
  console.log(
    'Highlighting text:',
    text.substring(0, 50) + '...',
    'with words:',
    words.map((w) => w.word),
  );

  // Create a pattern to match all highlight words (case-insensitive)
  const patterns = words.map((w) => w.word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')); // Escape regex special chars
  const regex = new RegExp(`(${patterns.join('|')})`, 'gi');

  const parts = text.split(regex);
  const elements: JSX.Element[] = [];

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (!part) continue;

    // Check if this part matches any highlight word
    const matchingWord = words.find((w) => w.word.toLowerCase() === part.toLowerCase());

    if (matchingWord) {
      elements.push(
        <TooltipProvider key={i}>
          <Tooltip>
            <TooltipTrigger asChild>
              <mark className="bg-yellow-200 hover:bg-yellow-300 cursor-help px-1 rounded">{part}</mark>
            </TooltipTrigger>
            <TooltipContent>
              <p className="max-w-xs text-sm">{matchingWord.rationale}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>,
      );
    } else {
      elements.push(<span key={i}>{part}</span>);
    }
  }

  return elements;
};

const componentFactory = (
  tag: keyof JSX.IntrinsicElements,
  className: string,
  highlightWords?: HighlightWord[],
  baseHighlight?: 'red' | 'yellow' | 'blue' | 'green' | 'none',
) => {
  const baseHighlightClass =
    baseHighlight && baseHighlight !== 'none'
      ? {
          red: 'bg-red-100',
          yellow: 'bg-yellow-100',
          blue: 'bg-blue-50',
          green: 'bg-green-100',
        }[baseHighlight]
      : '';

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const Component = ({ node, children, ...rest }: MarkdownComponentProps<typeof tag>) => {
    const Component = tag as unknown as ComponentType<MarkdownComponentProps<typeof tag>>;

    // Handle text content for highlighting
    const processChildren = (children: React.ReactNode): React.ReactNode => {
      if (typeof children === 'string' && highlightWords && highlightWords.length > 0) {
        return highlightText(children, highlightWords);
      }
      return children;
    };

    if (baseHighlight && baseHighlight !== 'none') {
      return (
        <Component {...rest} className={cn(className, rest.className)}>
          <div className={baseHighlightClass}>{processChildren(children)}</div>
        </Component>
      );
    }

    return (
      <Component {...rest} className={cn(className, rest.className)}>
        {processChildren(children)}
      </Component>
    );
  };

  Component.displayName = `MarkdownWithHighlights-${tag}`;
  return Component;
};

const createComponents = (
  highlightWords?: HighlightWord[],
  baseHighlight?: 'red' | 'yellow' | 'blue' | 'green' | 'none',
) => ({
  p: componentFactory('p', '', highlightWords, baseHighlight),
  h1: componentFactory('h1', 'text-2xl font-bold', highlightWords, baseHighlight),
  h2: componentFactory('h2', 'text-xl font-bold', highlightWords, baseHighlight),
  h3: componentFactory('h3', 'text-lg font-bold', highlightWords, baseHighlight),
  h4: componentFactory('h4', 'text-base font-bold', highlightWords, baseHighlight),
  h5: componentFactory('h5', 'text-sm font-bold', highlightWords, baseHighlight),
  h6: componentFactory('h6', 'text-xs font-bold', highlightWords, baseHighlight),
  ul: componentFactory('ul', 'list-disc', highlightWords, baseHighlight),
  ol: componentFactory('ol', 'list-decimal', highlightWords, baseHighlight),
  li: componentFactory('li', 'ml-4', highlightWords, baseHighlight),
  a: componentFactory('a', 'text-blue-600', highlightWords, baseHighlight),
  img: componentFactory('img', 'w-full', highlightWords, baseHighlight),
  blockquote: componentFactory('blockquote', 'border-l-4 border-gray-300 pl-4', highlightWords, baseHighlight),
  code: componentFactory('code', 'bg-gray-100 px-1 py-0.5 rounded', highlightWords, baseHighlight),
  pre: componentFactory('pre', 'bg-gray-100 px-1 py-0.5 rounded', highlightWords, baseHighlight),
  table: componentFactory('table', 'w-full', highlightWords, baseHighlight),
  thead: componentFactory('thead', 'bg-gray-100', highlightWords, baseHighlight),
  tbody: componentFactory('tbody', 'bg-gray-100', highlightWords, baseHighlight),
  tr: componentFactory('tr', 'bg-gray-100', highlightWords, baseHighlight),
  th: componentFactory('th', 'bg-gray-100', highlightWords, baseHighlight),
  td: componentFactory('td', 'bg-gray-100', highlightWords, baseHighlight),
  hr: componentFactory('hr', 'my-4', highlightWords, baseHighlight),
  br: componentFactory('br', '', highlightWords, baseHighlight),
  em: componentFactory('em', 'italic', highlightWords, baseHighlight),
  strong: componentFactory('strong', 'font-bold', highlightWords, baseHighlight),
  del: componentFactory('del', 'line-through', highlightWords, baseHighlight),
  ins: componentFactory('ins', 'underline', highlightWords, baseHighlight),
  sup: componentFactory('sup', 'text-sm', highlightWords, baseHighlight),
  sub: componentFactory('sub', 'text-sm', highlightWords, baseHighlight),
});

export function MarkdownWithHighlights(props: MarkdownWithHighlightsProps) {
  const { highlightWords, baseHighlight = 'none', ...rest } = props;

  const components = createComponents(highlightWords, baseHighlight);

  return <ReactMarkdown components={components} {...rest} />;
}
