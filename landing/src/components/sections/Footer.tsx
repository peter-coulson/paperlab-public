export function Footer() {
  return (
    <footer className="bg-deep-slate py-12">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="flex flex-col items-center gap-8">
          {/* Wordmark */}
          <a href="/" className="flex items-baseline gap-0">
            <span className="font-display text-lg font-semibold tracking-tight text-text-on-dark">
              Paper
            </span>
            <span className="font-display text-lg font-semibold tracking-tight text-indigo-light">
              Lab
            </span>
          </a>

          {/* Tagline */}
          <p className="font-body text-sm text-text-on-dark-muted">
            Built for students who want to understand their mistakes
          </p>

          {/* Links and Copyright */}
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:gap-8">
            <nav className="flex flex-wrap justify-center gap-6">
              <a
                href="/privacy"
                className="font-body text-sm text-text-on-dark-muted transition-colors hover:text-text-on-dark"
              >
                Privacy Policy
              </a>
              <a
                href="/terms"
                className="font-body text-sm text-text-on-dark-muted transition-colors hover:text-text-on-dark"
              >
                Terms of Service
              </a>
              <a
                href="/support"
                className="font-body text-sm text-text-on-dark-muted transition-colors hover:text-text-on-dark"
              >
                Support
              </a>
            </nav>
            <span className="font-body text-xs text-text-on-dark-muted/60">
              © 2026 PaperLab
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
