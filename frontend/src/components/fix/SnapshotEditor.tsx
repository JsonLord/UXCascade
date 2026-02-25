import { useRef } from 'react';
import type { EventSnapshot, HtmlPatch } from '../../types';

interface SnapshotEditorProps {
  snapshot: EventSnapshot;
  highlightSelector?: string;
  onPatchApply: (patch: HtmlPatch) => void;
}

export default function SnapshotEditor({
  snapshot,
  highlightSelector,
  onPatchApply,
}: SnapshotEditorProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Inject highlight style for the problem element
  const htmlWithHighlight = highlightSelector
    ? snapshot.rawHtml.replace(
        '</head>',
        `<style>
          ${highlightSelector} {
            outline: 3px solid #ef4444 !important;
            outline-offset: 2px !important;
            background: rgba(239,68,68,0.08) !important;
          }
        </style></head>`
      )
    : snapshot.rawHtml;

  function handleApplyTextChange(selector: string, newText: string) {
    onPatchApply({
      selector,
      action: 'replace_text',
      value: newText,
      name: null,
      rationale: 'Manual text edit via toolbar',
    });
  }

  void handleApplyTextChange; // used by toolbar (future)

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
        <span className="font-medium text-gray-600">Snapshot editor</span>
        <span className="text-gray-300">|</span>
        <span>Click an element in the preview to select it (coming soon)</span>
      </div>

      {/* Iframe preview */}
      <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
        <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border-b border-gray-200">
          <div className="flex gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-400" />
            <span className="w-3 h-3 rounded-full bg-yellow-400" />
            <span className="w-3 h-3 rounded-full bg-green-400" />
          </div>
          <span className="text-xs text-gray-400 ml-2 truncate">
            {snapshot.tabMetadata.url}
          </span>
        </div>
        <iframe
          ref={iframeRef}
          srcDoc={htmlWithHighlight}
          sandbox="allow-same-origin"
          title="Snapshot preview"
          className="w-full h-[480px]"
        />
      </div>

      {/* Screenshot fallback */}
      {snapshot.screenshot && (
        <details className="text-xs text-gray-400">
          <summary className="cursor-pointer hover:text-gray-600">
            Show original screenshot
          </summary>
          <img
            src={snapshot.screenshot}
            alt="Agent screenshot"
            className="mt-2 w-full rounded-lg border border-gray-200"
          />
        </details>
      )}
    </div>
  );
}
