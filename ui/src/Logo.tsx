type LogoProps = { compact?: boolean };

export function Logo({ compact = false }: LogoProps) {
  return (
    <a className="brand" href="/" aria-label="Seismic home">
      <svg className="brand-mark" viewBox="0 0 42 42" role="img" aria-label="Seismic fault line">
        <path className="mark-frame" d="M6 4.5h30l2.5 2.5v28L36 37.5H6L3.5 35V7z" />
        <path className="mark-fault" d="M7 24h8l3-8 5 15 4-10 2 3h6" />
        <circle className="mark-origin" cx="18" cy="16" r="2" />
      </svg>
      {!compact && <span>Seismic</span>}
    </a>
  );
}
