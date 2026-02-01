interface MarimoEmbedProps {
  src?: string;
}

export default function MarimoEmbed({ src }: MarimoEmbedProps) {
  if (!src) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4 text-slate-300">
        <p className="text-sm">
          Marimo embed is not configured. Set <code className="text-slate-200">NEXT_PUBLIC_MARIMO_URL</code>{' '}
          to your marimo share URL (e.g. <code className="text-slate-200">https://marimo.app/l/...</code>).
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-950/50">
      <iframe
        src={src}
        title="Marimo Weave Dashboard"
        width="100%"
        height="600"
        sandbox="allow-scripts allow-same-origin allow-downloads allow-popups allow-downloads-without-user-activation"
        allow="microphone"
        allowFullScreen
        className="w-full rounded-lg"
        style={{ border: '0' }}
      />
    </div>
  );
}
