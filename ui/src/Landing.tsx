import { ArrowRight, Braces, GitBranch, Route, ShieldCheck } from "lucide-react";
import { useEffect } from "react";
import { Logo } from "./Logo";

export function Landing() {
  useEffect(() => {
    const elements = [...document.querySelectorAll<HTMLElement>(".reveal")];
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.16 },
    );
    elements.forEach((element, index) => {
      element.style.transitionDelay = `${Math.min(index, 3) * 55}ms`;
      observer.observe(element);
    });
    return () => observer.disconnect();
  }, []);

  return (
    <main className="landing">
      <header className="landing-nav">
        <Logo />
        <nav aria-label="Primary navigation">
          <a href="#how">How it works</a>
          <a href="#hydradb">Why HydraDB</a>
          <a className="nav-action" href="/app">Open analyzer <ArrowRight size={16} /></a>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy reveal">
          <h1>Give every code change a graph-backed go or no-go.</h1>
          <p>
            Seismic turns a git diff into a safe, review or block decision with the exact
            HydraDB paths, required tests and entrypoints behind every claim.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="/app">Gate a change <ArrowRight size={18} /></a>
            <a className="text-action" href="#how">See the graph invariant</a>
          </div>
        </div>
        <HeroFaultMap />
      </section>

      <section className="principle-band reveal" aria-label="Core product principles">
        <div><Route /><strong>Exact paths</strong><span>Every impact includes its dependency route.</span></div>
        <div><GitBranch /><strong>Versioned snapshots</strong><span>Agents never query a half-built graph.</span></div>
        <div><ShieldCheck /><strong>Agent change gate</strong><span>Safe, review or block, with the reasons exposed.</span></div>
      </section>

      <section id="how" className="how-section">
        <div className="section-heading reveal">
          <span>A diff in, a defensible decision out</span>
          <h2>From repository to change gate.</h2>
        </div>
        <ol className="workflow-list">
          <li className="reveal"><b>01</b><div><strong>Index</strong><p>Parse files, symbols, calls, imports, tests, packages and entrypoints.</p></div></li>
          <li className="reveal"><b>02</b><div><strong>Resolve</strong><p>Choose the exact file or symbol from the active immutable snapshot.</p></div></li>
          <li className="reveal"><b>03</b><div><strong>Traverse</strong><p>Walk incoming dependency edges with HydraDB native bounded paths.</p></div></li>
          <li className="reveal"><b>04</b><div><strong>Decide</strong><p>Return safe, review or block with exact tests, entrypoints, owners and path evidence.</p></div></li>
        </ol>
      </section>

      <section id="hydradb" className="hydra-section reveal">
        <div className="hydra-copy">
          <Braces size={34} />
          <h2>The graph is the retrieval engine.</h2>
          <p>
            Similar text is not the same as structural relevance. A test can protect a function
            without sharing its vocabulary. Seismic uses HydraDB’s native SSpaths, MSpaths and
            SPpaths procedures to recover that relationship and return the whole path.
          </p>
        </div>
        <div className="direction-diagram" aria-label="Dependency direction explanation">
          <span className="diagram-node">caller</span>
          <span className="diagram-edge">CALLS →</span>
          <span className="diagram-node origin">callee</span>
          <span className="diagram-return">blast radius walks incoming ←</span>
        </div>
      </section>

      <footer className="landing-footer">
        <Logo />
        <span>Built by Himanshu Kumar for Hack Hydra Track 02B.</span>
        <a href="/app">Open analyzer</a>
      </footer>
    </main>
  );
}

function HeroFaultMap() {
  return (
    <div className="hero-map reveal" aria-label="Illustration of code change propagation">
      <div className="map-header"><span>Change propagation</span><code>incoming · max 4 hops</code></div>
      <svg viewBox="0 0 680 520" role="img" aria-label="A changed pricing function reaching callers, tests and an entrypoint">
        <g className="map-grid">
          {Array.from({ length: 9 }, (_, i) => <line key={`v${i}`} x1={i * 85} y1="0" x2={i * 85} y2="520" />)}
          {Array.from({ length: 7 }, (_, i) => <line key={`h${i}`} x1="0" y1={i * 86.6} x2="680" y2={i * 86.6} />)}
        </g>
        <g className="map-paths">
          <path d="M120 260C210 260 205 130 315 130S425 88 540 88" />
          <path d="M120 260C220 260 220 260 330 260S440 220 540 220" />
          <path d="M120 260C205 260 215 385 330 385S435 430 550 430" />
          <circle className="map-pulse" r="5"><animateMotion dur="3.2s" repeatCount="indefinite" path="M120 260C220 260 220 260 330 260S440 220 540 220" /></circle>
        </g>
        <g className="map-node origin" transform="translate(38 226)"><rect width="164" height="68" rx="8"/><text x="15" y="22">CHANGE</text><text x="15" y="47">pricing.calculate</text></g>
        <g className="map-node" transform="translate(274 96)"><rect width="140" height="68" rx="8"/><text x="15" y="22">CALLER</text><text x="15" y="47">checkout.total</text></g>
        <g className="map-node" transform="translate(284 226)"><rect width="140" height="68" rx="8"/><text x="15" y="22">CALLER</text><text x="15" y="47">service.handler</text></g>
        <g className="map-node" transform="translate(280 351)"><rect width="140" height="68" rx="8"/><text x="15" y="22">TEST</text><text x="15" y="47">test_total</text></g>
        <g className="map-node" transform="translate(500 54)"><rect width="142" height="68" rx="8"/><text x="15" y="22">ENTRYPOINT</text><text x="15" y="47">sample</text></g>
        <g className="map-node" transform="translate(500 186)"><rect width="142" height="68" rx="8"/><text x="15" y="22">API PATH</text><text x="15" y="47">/checkout</text></g>
        <g className="map-node" transform="translate(500 396)"><rect width="142" height="68" rx="8"/><text x="15" y="22">TEST FILE</text><text x="15" y="47">test_checkout.py</text></g>
      </svg>
    </div>
  );
}
