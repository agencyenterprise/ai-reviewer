'use client';

import { Markdown } from '@/components/markdown';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { convertMarkdownToDocx, downloadDocx } from '@mohtasham/md-to-docx';
import { ChevronDown, Download, FileText, Loader2, Printer } from 'lucide-react';
import { useRef, useState } from 'react';
import { toast } from 'sonner';

interface MarkdownDownloadButtonProps {
  /** Markdown source to export. */
  markdown: string;
  /** Base file name (without extension) used for the downloaded files. */
  fileName: string;
}

/**
 * A "Download" dropdown that exports the given markdown as DOCX or PDF, entirely
 * client-side. DOCX conversion uses `@mohtasham/md-to-docx`; PDF uses a print
 * window populated with the rendered markdown and the current page styles.
 */
export function MarkdownDownloadButton({ markdown, fileName }: MarkdownDownloadButtonProps) {
  const [isConverting, setIsConverting] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleDownloadDocx = async () => {
    setIsConverting(true);
    try {
      const blob = await convertMarkdownToDocx(markdown, {
        style: {
          fontFamily: 'Georgia',
        },
      });
      downloadDocx(blob, `${fileName}.docx`);
    } catch (error) {
      console.error('Failed to convert markdown to DOCX:', error);
      toast.error('Failed to generate DOCX file');
    } finally {
      setIsConverting(false);
    }
  };

  const handleDownloadPdf = () => {
    if (!contentRef.current) return;
    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      toast.error('Please allow pop-ups to download PDF');
      return;
    }

    const styles = Array.from(document.styleSheets)
      .map((sheet) => {
        try {
          return Array.from(sheet.cssRules)
            .map((rule) => rule.cssText)
            .join('\n');
        } catch {
          return '';
        }
      })
      .join('\n');

    printWindow.document.write(`<!DOCTYPE html>
<html><head><title>${fileName}</title><style>${styles}</style></head>
<body class="p-8 text-sm">${contentRef.current.innerHTML}</body></html>`);
    printWindow.document.close();
    printWindow.addEventListener('afterprint', () => printWindow.close());
    printWindow.print();
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" disabled={isConverting}>
            {isConverting ? <Loader2 className="animate-spin" /> : <Download />}
            {isConverting ? 'Generating...' : 'Download'}
            <ChevronDown />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={handleDownloadDocx} disabled={isConverting}>
            <FileText />
            Download as DOCX
          </DropdownMenuItem>
          <DropdownMenuItem onClick={handleDownloadPdf}>
            <Printer />
            Download as PDF
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Off-screen render used solely as the source HTML for the PDF export. */}
      <div ref={contentRef} className="hidden">
        <Markdown>{markdown}</Markdown>
      </div>
    </>
  );
}
