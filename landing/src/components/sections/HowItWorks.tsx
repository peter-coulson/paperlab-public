import Image from "next/image";

const steps = [
  {
    number: 1,
    title: "Select your paper",
    description:
      "Choose from past papers organized by exam session. Track which questions you've completed",
    image: "/images/paper_upload.jpeg",
  },
  {
    number: 2,
    title: "Photo your work",
    description:
      "Snap your handwritten answer for each question. Works with any paper and pen",
    image: "/images/question_upload.png",
  },
  {
    number: 3,
    title: "See your results",
    description:
      "Get your grade instantly, then drill into any question to see exactly where marks were gained or lost",
    image: "/images/paper_results.jpeg",
  },
];

export function HowItWorks() {
  return (
    <section
      className="py-20 md:py-24 lg:py-32"
      style={{
        background:
          "linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%)",
      }}
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <h2 className="font-display text-center text-[28px] md:text-[32px] lg:text-[36px] font-semibold leading-[1.2] tracking-[-0.01em] text-text-on-dark">
          Three steps
        </h2>

        <div className="mt-16 grid gap-12 md:grid-cols-3 md:gap-8 lg:gap-12">
          {steps.map((step) => (
            <div
              key={step.number}
              className="group flex flex-col items-center text-center transition-transform duration-300 hover:-translate-y-1"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo text-lg font-semibold text-white">
                {step.number}
              </div>

              <div className="mt-8 w-full overflow-hidden rounded-xl shadow-lg transition-shadow duration-300 group-hover:shadow-xl">
                <Image
                  src={step.image}
                  alt={step.title}
                  width={400}
                  height={300}
                  className="h-auto w-full object-cover"
                />
              </div>

              <h3 className="mt-6 font-display text-xl font-medium text-text-on-dark">
                {step.title}
              </h3>

              <p className="mt-3 text-sm leading-relaxed text-text-on-dark-muted">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
