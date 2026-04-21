import Image from "next/image";

export function Solution() {
  return (
    <section className="bg-white py-20 md:py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Text Content */}
          <div>
            <h2 className="font-display text-[32px] font-semibold leading-[1.2] tracking-[-0.01em] text-text-primary md:text-[40px] lg:text-[48px]">
              Your working, step by step
            </h2>

            <div className="mt-8 space-y-6 text-lg leading-[1.7] text-text-secondary">
              <p>
                PaperLab reads your handwritten working—not just the final
                answer.
              </p>

              <p>
                Every mark is explained. When you lose one, you see exactly
                which criterion wasn&apos;t met and why.
              </p>
            </div>
          </div>

          {/* Screenshot */}
          <div className="relative">
            <Image
              src="/images/mark_results.jpeg"
              alt="Detailed marking breakdown showing method marks and accuracy marks with green and amber indicators"
              width={800}
              height={600}
              className="rounded-xl shadow-lg"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
