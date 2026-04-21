import { Header } from "@/components/sections/Header";
import { Footer } from "@/components/sections/Footer";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Support | PaperLab",
  description: "Get help with PaperLab - contact support, FAQs, and usage guide",
};

export default function SupportPage() {
  return (
    <main>
      <Header variant="solid" />
      <div className="bg-warm-white pt-24 pb-16 md:pt-32 md:pb-24">
        <div className="mx-auto max-w-3xl px-6 lg:px-8">
          <h1 className="font-display text-3xl font-semibold text-text-primary md:text-4xl">
            Support
          </h1>
          <p className="mt-4 font-body text-text-secondary">
            We&apos;re here to help you get the most out of PaperLab
          </p>

          <div className="mt-12 space-y-12">
            {/* Contact Section */}
            <section className="rounded-2xl bg-white p-8 shadow-md">
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Contact Us
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                Have a question, feedback, or need help? Reach out to our support team.
              </p>
              <div className="mt-6">
                <a
                  href="mailto:support@mypaperlab.com"
                  className="inline-flex items-center gap-2 rounded-lg bg-indigo-deep px-6 py-3 font-medium text-white shadow-indigo transition-all hover:bg-indigo-deep/90 hover:shadow-lg"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="h-5 w-5"
                  >
                    <path d="M1.5 8.67v8.58a3 3 0 003 3h15a3 3 0 003-3V8.67l-8.928 5.493a3 3 0 01-3.144 0L1.5 8.67z" />
                    <path d="M22.5 6.908V6.75a3 3 0 00-3-3h-15a3 3 0 00-3 3v.158l9.714 5.978a1.5 1.5 0 001.572 0L22.5 6.908z" />
                  </svg>
                  support@mypaperlab.com
                </a>
              </div>
              <p className="mt-4 font-body text-sm text-text-muted">
                We typically respond within 24-48 hours
              </p>
            </section>

            {/* FAQ Section */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Frequently Asked Questions
              </h2>
              <div className="mt-6 space-y-6">
                <div className="rounded-xl bg-white p-6 shadow-sm">
                  <h3 className="font-display font-semibold text-text-primary">
                    What subjects does PaperLab support?
                  </h3>
                  <p className="mt-2 font-body text-text-secondary">
                    PaperLab currently supports GCSE Maths, with plans to expand to other
                    STEM subjects in the future.
                  </p>
                </div>

                <div className="rounded-xl bg-white p-6 shadow-sm">
                  <h3 className="font-display font-semibold text-text-primary">
                    How accurate is the AI marking?
                  </h3>
                  <p className="mt-2 font-body text-text-secondary">
                    Our AI uses official exam mark schemes to assess your answers and provide
                    helpful feedback. It&apos;s designed as a learning tool rather than official
                    assessment. Use the marks as guidance to understand your strengths and areas
                    for improvement.
                  </p>
                </div>

                <div className="rounded-xl bg-white p-6 shadow-sm">
                  <h3 className="font-display font-semibold text-text-primary">
                    Are my exam photos stored securely?
                  </h3>
                  <p className="mt-2 font-body text-text-secondary">
                    Yes. All images are transmitted using encrypted connections and stored
                    securely on Cloudflare R2. Staging images are automatically deleted after
                    24 hours. See our Privacy Policy for full details.
                  </p>
                </div>

                <div className="rounded-xl bg-white p-6 shadow-sm">
                  <h3 className="font-display font-semibold text-text-primary">
                    What platforms is PaperLab available on?
                  </h3>
                  <p className="mt-2 font-body text-text-secondary">
                    PaperLab is available on the web at app.mypaperlab.com. The iOS app is currently
                    in beta via TestFlight with a full release coming soon. Android is in development.
                  </p>
                </div>

                <div className="rounded-xl bg-white p-6 shadow-sm">
                  <h3 className="font-display font-semibold text-text-primary">
                    How do I delete my account?
                  </h3>
                  <p className="mt-2 font-body text-text-secondary">
                    You can delete your account and all associated data from within the app
                    in your account settings. Alternatively, email us at support@mypaperlab.com
                    and we&apos;ll process your request within 30 days.
                  </p>
                </div>
              </div>
            </section>

            {/* Usage Guide */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                How to Use PaperLab
              </h2>
              <div className="mt-6 space-y-4">
                <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-deep text-sm font-semibold text-white">
                    1
                  </div>
                  <div>
                    <h3 className="font-display font-semibold text-text-primary">
                      Take a Photo
                    </h3>
                    <p className="mt-1 font-body text-text-secondary">
                      Use your camera to photograph your completed exam paper. Make sure the
                      image is clear and all your answers are visible.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-deep text-sm font-semibold text-white">
                    2
                  </div>
                  <div>
                    <h3 className="font-display font-semibold text-text-primary">
                      Select the Exam
                    </h3>
                    <p className="mt-1 font-body text-text-secondary">
                      Choose the exam board, subject, and specific paper you&apos;ve completed.
                      This helps our AI use the correct mark scheme.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-deep text-sm font-semibold text-white">
                    3
                  </div>
                  <div>
                    <h3 className="font-display font-semibold text-text-primary">
                      Get Your Results
                    </h3>
                    <p className="mt-1 font-body text-text-secondary">
                      Within moments, you&apos;ll receive your marked paper with scores,
                      detailed feedback, and analysis of any misconceptions.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4 rounded-xl bg-white p-6 shadow-sm">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-deep text-sm font-semibold text-white">
                    4
                  </div>
                  <div>
                    <h3 className="font-display font-semibold text-text-primary">
                      Learn and Improve
                    </h3>
                    <p className="mt-1 font-body text-text-secondary">
                      Review the misconception analysis to understand why certain answers
                      were incorrect. Use this insight to target your revision effectively.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            {/* Tips */}
            <section className="rounded-2xl bg-stone p-8">
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Tips for Best Results
              </h2>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Ensure good lighting when photographing your paper</li>
                <li>Keep the camera steady to avoid blurry images</li>
                <li>Include the full page in each photo</li>
                <li>Make sure your handwriting is clearly visible</li>
                <li>Use official past papers from exam board websites for practice</li>
              </ul>
            </section>
          </div>
        </div>
      </div>
      <Footer />
    </main>
  );
}
