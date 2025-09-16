import ReactMarkdown from 'react-markdown';

const components = {
  p: (props: React.ComponentProps<'p'>) => <p {...props} />,
  h1: (props: React.ComponentProps<'h1'>) => <h1 className="text-2xl font-bold" {...props} />,
  h2: (props: React.ComponentProps<'h2'>) => <h2 className="text-xl font-bold" {...props} />,
  h3: (props: React.ComponentProps<'h3'>) => <h3 className="text-lg font-bold" {...props} />,
  h4: (props: React.ComponentProps<'h4'>) => <h4 className="text-base font-bold" {...props} />,
  h5: (props: React.ComponentProps<'h5'>) => <h5 className="text-sm font-bold" {...props} />,
  h6: (props: React.ComponentProps<'h6'>) => <h6 className="text-xs font-bold" {...props} />,
  ul: (props: React.ComponentProps<'ul'>) => <ul className="list-disc" {...props} />,
  ol: (props: React.ComponentProps<'ol'>) => <ol className="list-decimal" {...props} />,
  li: (props: React.ComponentProps<'li'>) => <li className="ml-4" {...props} />,
  a: (props: React.ComponentProps<'a'>) => <a className="text-blue-600" {...props} />,
  img: (props: React.ComponentProps<'img'>) => <img className="w-full" {...props} />,
  blockquote: (props: React.ComponentProps<'blockquote'>) => (
    <blockquote className="border-l-4 border-gray-300 pl-4" {...props} />
  ),
  code: (props: React.ComponentProps<'code'>) => <code className="bg-gray-100 px-1 py-0.5 rounded" {...props} />,
  pre: (props: React.ComponentProps<'pre'>) => <pre className="bg-gray-100 px-1 py-0.5 rounded" {...props} />,
  table: (props: React.ComponentProps<'table'>) => <table className="w-full" {...props} />,
  thead: (props: React.ComponentProps<'thead'>) => <thead className="bg-gray-100" {...props} />,
  tbody: (props: React.ComponentProps<'tbody'>) => <tbody className="bg-gray-100" {...props} />,
  tr: (props: React.ComponentProps<'tr'>) => <tr className="bg-gray-100" {...props} />,
  th: (props: React.ComponentProps<'th'>) => <th className="bg-gray-100" {...props} />,
  td: (props: React.ComponentProps<'td'>) => <td className="bg-gray-100" {...props} />,
  hr: (props: React.ComponentProps<'hr'>) => <hr className="my-4" {...props} />,
  br: (props: React.ComponentProps<'br'>) => <br {...props} />,
  em: (props: React.ComponentProps<'em'>) => <em className="italic" {...props} />,
  strong: (props: React.ComponentProps<'strong'>) => <strong className="font-bold" {...props} />,
  del: (props: React.ComponentProps<'del'>) => <del className="line-through" {...props} />,
  ins: (props: React.ComponentProps<'ins'>) => <ins className="underline" {...props} />,
  sup: (props: React.ComponentProps<'sup'>) => <sup className="text-sm" {...props} />,
  sub: (props: React.ComponentProps<'sub'>) => <sub className="text-sm" {...props} />,
};

export function Markdown(props: React.ComponentProps<typeof ReactMarkdown>) {
  return <ReactMarkdown components={components} {...props} />;
}
