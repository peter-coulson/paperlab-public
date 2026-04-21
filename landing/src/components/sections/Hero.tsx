import Image from "next/image";

export function Hero() {
  return (
    <section
      className="relative bg-deep-slate overflow-hidden pt-14 md:pt-16"
      style={{
        backgroundImage:
          "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(102, 126, 234, 0.15) 0%, transparent 70%)",
      }}
    >
      <div className="mx-auto max-w-7xl px-6 py-20 md:py-24 lg:px-8 lg:py-32">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Text Content */}
          <div className="text-center lg:text-left">
            <h1 className="font-display text-[40px] font-semibold leading-[1.1] tracking-[-0.02em] text-text-on-dark md:text-[56px] lg:text-[72px]">
              Know exactly where your working went wrong
            </h1>

            <p className="mt-4 text-sm font-medium uppercase tracking-[0.15em] text-indigo-light">
              GCSE Maths Past Paper Marking
            </p>

            <p className="mt-6 text-lg leading-[1.6] text-text-on-dark-muted md:text-xl">
              Photograph your working. Get instant marking with feedback on
              every method mark and accuracy mark
            </p>

            <div className="mt-10 flex flex-col items-center gap-5 sm:flex-row sm:gap-4 lg:items-start">
              {/* Primary: iOS Download */}
              <a
                href="https://apps.apple.com/gb/app/paperlab/id6755894915"
                className="group relative inline-flex items-center gap-3 rounded-xl bg-white px-6 py-4 font-medium text-deep-slate shadow-lg shadow-white/10 transition-all duration-200 hover:shadow-xl hover:shadow-white/20 hover:-translate-y-0.5"
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
                className="group relative inline-flex items-center gap-3 rounded-xl bg-indigo-deep/20 px-6 py-4 font-medium text-white ring-1 ring-indigo-light/30 transition-all duration-200 hover:bg-indigo-deep/30 hover:ring-indigo-light/50 hover:-translate-y-0.5"
              >
                <svg className="h-6 w-6 text-indigo-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M2 12h20"/>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
                <span className="flex flex-col items-start leading-tight">
                  <span className="text-[11px] font-normal text-indigo-light/70">Try instantly in</span>
                  <span className="text-lg -mt-0.5">Your Browser</span>
                </span>
              </a>
            </div>
          </div>

          {/* Hero Screenshot */}
          <div className="relative mx-auto w-full max-w-md lg:max-w-none">
            <Image
              src="/images/question_plus_results.jpeg"
              alt="PaperLab app showing a maths question with LaTeX rendering and detailed marking results"
              width={600}
              height={800}
              priority
              className="rounded-xl shadow-xl"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
