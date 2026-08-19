import {
  ArrowRight,
  Braces,
  Check,
  Database,
  FileDiff,
  FileWarning,
  Gauge,
  Network,
  Route,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import dashboardEvidence from "../../docs/assets/dashboard-self-analysis.png";
import { Logo } from "./Logo";

const GITHUB_URL = "https://github.com/himanshu748/seismic-hydradb";

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
          <a href="#product">Product</a>
          <a href="#risk">Risk</a>
          <a href="#hydradb">HydraDB</a>
          <a className="nav-action" href="/app">Open analyzer <ArrowRight size={16} /></a>
        </nav>
      </header>

      <section className="hero">
        <div className="hero-copy reveal">
          <span className="hero-kicker">Graph-native change gate</span>
          <h1><span>Know what breaks</span><span>before the edit.</span></h1>
          <p>
            Seismic turns a git diff into exact impact paths, required tests and a safe,
            review or block decision.
          </p>
          <div className="hero-actions">
            <a className="primary-action" href="/app">Open analyzer <ArrowRight size={18} /></a>
            <a className="text-action" href="#evidence">Inspect evidence</a>
          </div>
        </div>
        <HeroFaultMap />
      </section>

      <section className="seismic-proof-rail reveal" aria-label="Verified product evidence">
        <div><strong>1.000</strong><span>Graph MRR</span></div>
        <div><strong>10 / 10</strong><span>Exact paths valid</span></div>
        <div><strong>3 / 3</strong><span>Real repositories</span></div>
        <div><strong>25 / 25</strong><span>Stress recoveries</span></div>
      </section>

      <section id="product" className="product-proof-section reveal" aria-labelledby="product-proof-title">
        <div className="product-proof-copy">
          <h2 id="product-proof-title">The decision and its proof stay on the same screen.</h2>
          <p>
            A real Seismic analysis shows the changed symbol, every supported impact,
            required verification and the exact HydraDB path connecting them.
          </p>
        </div>
        <figure className="product-frame">
          <div className="product-frame-bar">
            <span>Seismic change gate</span>
            <code>HydraDB connected</code>
          </div>
          <img
            src={dashboardEvidence}
            width="1280"
            height="720"
            loading="lazy"
            alt="Seismic analyzer showing a review gate, affected artifacts and an exact dependency path for a real code change"
          />
          <figcaption>
            Self-analysis of Seismic’s own HTTP entrypoint, resolved through the active repository snapshot.
          </figcaption>
        </figure>
      </section>

      <section className="seismic-statement reveal">
        <p>Similarity finds nearby words. Seismic finds the code that breaks.</p>
      </section>

      <section id="workflow" className="workflow-section">
        <div className="workflow-intro reveal">
          <h2>One diff. Four graph operations. One decision.</h2>
          <p>Every supported impact stays attached to the path that proves it.</p>
        </div>
        <div className="workflow-stages">
          <article className="reveal"><FileDiff size={22} /><strong>Index the checkout</strong><p>Build an immutable snapshot of files, symbols, calls, imports, tests and entrypoints.</p></article>
          <article className="reveal"><Route size={22} /><strong>Resolve the change</strong><p>Map each diff hunk to an exact artifact in the active snapshot.</p></article>
          <article className="reveal"><Network size={22} /><strong>Traverse dependents</strong><p>Walk bounded incoming paths through HydraDB’s native graph procedures.</p></article>
          <article className="reveal"><ShieldCheck size={22} /><strong>Issue the gate</strong><p>Return safe, review or block with required tests, entrypoints and inspectable reasons.</p></article>
        </div>
      </section>

      <section id="risk" className="risk-story reveal" aria-labelledby="risk-title">
        <div className="risk-copy">
          <Gauge size={30} aria-hidden="true" />
          <h2 id="risk-title">68 means review, not the maximum.</h2>
          <p>
            Seismic scores evidence from 0 to 100. This direct function impact earns 68,
            while automatic blocking begins at 75.
          </p>
          <small>An exact prior incident pair blocks regardless of the numeric score.</small>
        </div>
        <div className="risk-equation" aria-label="Risk score breakdown: 45 proximity plus 15 fan-in plus 8 function criticality plus 0 incident evidence equals 68 out of 100">
          <div className="risk-total"><strong>68</strong><span>out of 100</span><b>Review</b></div>
          <dl>
            <div><dt>Direct proximity</dt><dd>+45</dd></div>
            <div><dt>Maximum path fan-in</dt><dd>+15</dd></div>
            <div><dt>Function criticality</dt><dd>+8</dd></div>
            <div><dt>Incident evidence</dt><dd>+0</dd></div>
          </dl>
          <div className="risk-threshold"><span>Block threshold</span><strong>75</strong></div>
        </div>
      </section>

      <section className="fallback-story reveal" aria-labelledby="fallback-title">
        <div className="fallback-copy">
          <FileWarning size={30} aria-hidden="true" />
          <span className="section-kicker">Conservative fallback</span>
          <h2 id="fallback-title">Missing evidence becomes a receipt, not a green light.</h2>
          <p>
            If a target cannot resolve or the active snapshot reports parser gaps, Seismic
            withholds <code>safe</code>, returns <code>review</code> and writes the reason to HydraDB.
          </p>
        </div>
        <div className="fallback-receipt" aria-label="Example durable Seismic fallback receipt">
          <header><span>DecisionReceipt</span><code>stored in HydraDB</code></header>
          <dl>
            <div><dt>Decision</dt><dd>Review</dd></div>
            <div><dt>Evidence</dt><dd>Incomplete</dd></div>
            <div><dt>Supported paths</dt><dd>0</dd></div>
            <div><dt>Safe issued</dt><dd>No</dd></div>
          </dl>
          <p>Target unresolved. Safe decision withheld and fallback logged.</p>
          <footer><code>DecisionReceipt</code><span>→ EVALUATED_SNAPSHOT →</span><code>Snapshot</code></footer>
        </div>
      </section>

      <section id="evidence" className="evidence-story reveal">
        <div className="evidence-copy">
          <span className="section-kicker">Structural evidence</span>
          <h2>Path proof beats resemblance.</h2>
          <p>
            A test can protect a function without sharing its vocabulary. Seismic returns the
            exact code path instead of guessing from text similarity.
          </p>
        </div>
        <div className="evidence-comparison" aria-label="Graph retrieval compared with text similarity">
          <div className="graph-result"><strong>1.000</strong><span>Graph precision and recall</span><small>10 of 10 supported tasks returned an exact valid path.</small></div>
          <div><strong>0.132</strong><span>TF-IDF precision and recall</span><small>Same tasks, same candidate set, no structural graph.</small></div>
        </div>
      </section>

      <section id="hydradb" className="hydra-section reveal">
        <div className="hydra-copy">
          <Braces size={34} />
          <h2>HydraDB is the path engine.</h2>
          <p>
            Seismic stores immutable repository snapshots and typed code relationships, then
            calls native SSpaths, MSpaths and SPpaths to recover bounded evidence. Every gate also
            writes a DecisionReceipt linked to the snapshot it evaluated.
          </p>
          <div className="procedure-list" aria-label="Native HydraDB procedures">
            <code>algo.SSpaths</code><code>algo.MSpaths</code><code>algo.SPpaths</code>
          </div>
        </div>
        <div className="direction-diagram" aria-label="Dependency direction explanation">
          <span className="diagram-node">caller</span>
          <span className="diagram-edge">CALLS →</span>
          <span className="diagram-node origin">callee</span>
          <span className="diagram-return">blast radius walks incoming ←</span>
        </div>
      </section>

      <section className="scale-section reveal">
        <div>
          <Database size={26} />
          <h2>Tested beyond the demo graph.</h2>
          <p>Fresh-store proof uses the same Bolt driver and path engine as the product.</p>
        </div>
        <dl>
          <div><dt>Artifacts</dt><dd>5,000</dd></div>
          <div><dt>Relationships</dt><dd>20,000</dd></div>
          <div><dt>Supported real-repo impacts</dt><dd>49</dd></div>
          <div><dt>Returned paths validated</dt><dd>All</dd></div>
        </dl>
      </section>

      <section className="seismic-cta reveal">
        <Logo />
        <h2>Make the agent prove the blast radius.</h2>
        <p>Index a checkout, paste a diff and inspect every supported impact before code changes.</p>
        <a className="primary-action" href="/app">Open analyzer <ArrowRight size={18} /></a>
      </section>

      <footer className="landing-footer">
        <div className="footer-product">
          <Logo />
          <p>Graph-native blast-radius evidence for coding agents.</p>
        </div>
        <div className="footer-meta">
          <span>Built by Himanshu Kumar for Hack Hydra Track 02B.</span>
          <nav aria-label="Footer navigation">
            <a href={GITHUB_URL} target="_blank" rel="noreferrer">GitHub</a>
            <a href="#hydradb">HydraDB</a>
            <a href="/app">Open analyzer</a>
          </nav>
        </div>
      </footer>
    </main>
  );
}

function HeroFaultMap() {
  const [traced, setTraced] = useState(false);

  return (
    <div className={`hero-map reveal ${traced ? "traced" : ""}`} aria-label="Interactive code change propagation">
      <div className="map-header"><span>Change propagation</span><code>incoming, max 4 hops</code></div>
      <svg viewBox="0 0 680 520" role="img" aria-label="A changed pricing function reaching callers, tests and an entrypoint">
        <g className="map-grid">
          {Array.from({ length: 9 }, (_, i) => <line key={`v${i}`} x1={i * 85} y1="0" x2={i * 85} y2="520" />)}
          {Array.from({ length: 7 }, (_, i) => <line key={`h${i}`} x1="0" y1={i * 86.6} x2="680" y2={i * 86.6} />)}
        </g>
        <g className="map-paths">
          <path d="M120 260C210 260 205 130 315 130S425 88 540 88" />
          <path d="M120 260C220 260 220 260 330 260S440 220 540 220" />
          <path d="M120 260C205 260 215 385 330 385S435 430 550 430" />
        </g>
        <g className="map-node origin" transform="translate(38 226)"><rect width="164" height="68" rx="8"/><text x="15" y="22">CHANGE</text><text x="15" y="47">pricing.calculate</text></g>
        <g className="map-node" transform="translate(274 96)"><rect width="140" height="68" rx="8"/><text x="15" y="22">CALLER</text><text x="15" y="47">checkout.total</text></g>
        <g className="map-node" transform="translate(284 226)"><rect width="140" height="68" rx="8"/><text x="15" y="22">CALLER</text><text x="15" y="47">service.handler</text></g>
        <g className="map-node" transform="translate(280 351)"><rect width="140" height="68" rx="8"/><text x="15" y="22">TEST</text><text x="15" y="47">test_total</text></g>
        <g className="map-node" transform="translate(500 54)"><rect width="142" height="68" rx="8"/><text x="15" y="22">ENTRYPOINT</text><text x="15" y="47">sample</text></g>
        <g className="map-node" transform="translate(500 186)"><rect width="142" height="68" rx="8"/><text x="15" y="22">API PATH</text><text x="15" y="47">/checkout</text></g>
        <g className="map-node" transform="translate(500 396)"><rect width="142" height="68" rx="8"/><text x="15" y="22">TEST FILE</text><text x="15" y="47">test_checkout.py</text></g>
      </svg>
      <div className="map-control">
        <span aria-live="polite">{traced ? <><Check size={15} /> Review: 5 supported impacts</> : "Trace incoming dependency paths"}</span>
        <button type="button" onClick={() => setTraced((active) => !active)}>{traced ? "Reset trace" : "Run path trace"}</button>
      </div>
    </div>
  );
}
