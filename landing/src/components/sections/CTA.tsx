export function CTA() {
  return (
    <section
      className="py-20 md:py-24 lg:py-32"
      style={{
        background: "linear-gradient(135deg, #4F46E5 0%, #667EEA 100%)",
      }}
    >
      <div className="mx-auto max-w-3xl px-6 text-center lg:px-8">
        <h2 className="font-display text-[28px] font-semibold leading-tight text-white md:text-[32px] lg:text-[36px]">
          See where the marks went
        </h2>

        <p className="mt-4 text-lg text-white/80">
          Instant feedback on your GCSE Maths working
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-5 sm:flex-row sm:gap-4">
          {/* Primary: iOS Download */}
          <a
            href="https://apps.apple.com/gb/app/paperlab/id6755894915"
            className="group relative inline-flex items-center gap-3 rounded-xl bg-white px-6 py-4 font-medium text-deep-slate shadow-lg shadow-black/10 transition-all duration-200 hover:shadow-xl hover:shadow-black/20 hover:-translate-y-0.5"
          >
            <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
            </svg>
            <span className="flex flex-col items-start leading-tight">
              <span className="text-[11px] font-normal opacity-70">Download on the</span>
              <span className="text-lg -mt-0.5">App Store</span>
            </span>
          </a>

          {/* Secondary: Web App */}
          <a
            href="https://app.mypaperlab.com"
            className="group relative inline-flex items-center gap-3 rounded-xl bg-white/10 px-6 py-4 font-medium text-white ring-1 ring-white/30 transition-all duration-200 hover:bg-white/20 hover:ring-white/50 hover:-translate-y-0.5"
          >
            <svg className="h-6 w-6 text-white/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M2 12h20"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
            </svg>
            <span className="flex flex-col items-start leading-tight">
              <span className="text-[11px] font-normal text-white/60">Try instantly in</span>
              <span className="text-lg -mt-0.5">Your Browser</span>
            </span>
          </a>
        </div>
      </div>
    </section>
  );
}
