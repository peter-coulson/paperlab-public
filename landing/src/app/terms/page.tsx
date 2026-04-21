import { Header } from "@/components/sections/Header";
import { Footer } from "@/components/sections/Footer";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service | PaperLab",
  description: "PaperLab terms of service and conditions of use",
};

export default function TermsPage() {
  return (
    <main>
      <Header variant="solid" />
      <div className="bg-warm-white pt-24 pb-16 md:pt-32 md:pb-24">
        <div className="mx-auto max-w-3xl px-6 lg:px-8">
          <h1 className="font-display text-3xl font-semibold text-text-primary md:text-4xl">
            Terms of Service
          </h1>
          <p className="mt-4 font-body text-text-secondary">
            Last updated: January 19, 2026
          </p>

          <div className="mt-12 space-y-10">
            {/* Agreement */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Agreement to Terms
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                By accessing or using PaperLab, you agree to be bound by these Terms of Service.
                If you do not agree with any part of these terms, you may not use our service.
              </p>
            </section>

            {/* Educational Use */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Educational Use Only
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                PaperLab is designed exclusively for educational purposes. The service is
                intended to help students learn from their exam work by providing AI-powered
                marking and misconception analysis.
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Use PaperLab only for legitimate educational self-assessment</li>
                <li>Do not use the service for official examination purposes</li>
                <li>Do not use the service to gain unfair advantages in assessed work</li>
                <li>Results are for learning purposes and should not replace official marking</li>
              </ul>
            </section>

            {/* Copyright */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Copyright and Exam Papers
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                Exam papers and mark schemes are typically protected by copyright. When using
                PaperLab:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>
                  You are responsible for ensuring you have the right to use any exam materials
                  you photograph
                </li>
                <li>
                  Many past papers are freely available from exam boards for personal study use
                </li>
                <li>
                  Do not upload exam papers during live examination periods
                </li>
                <li>
                  We process images solely for providing marking feedback and do not redistribute
                  exam content
                </li>
              </ul>
            </section>

            {/* Student Work Ownership */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Student Work Ownership
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                You retain full ownership of your original work and answers that you submit
                through PaperLab. By using our service:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>You grant us a limited license to process your submissions for marking</li>
                <li>Your original work remains your intellectual property</li>
                <li>We will not share your work with third parties</li>
                <li>We will not use your work for training purposes without explicit consent</li>
              </ul>
            </section>

            {/* User Responsibilities */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                User Responsibilities
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                As a user of PaperLab, you agree to:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Provide accurate information when creating your account</li>
                <li>Keep your account credentials secure</li>
                <li>Not share your account with others</li>
                <li>Not attempt to circumvent, disable, or interfere with the service</li>
                <li>Not use the service for any unlawful purpose</li>
                <li>Not upload inappropriate, offensive, or harmful content</li>
                <li>Report any bugs or vulnerabilities responsibly</li>
              </ul>
            </section>

            {/* AI Disclaimer */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                AI-Powered Marking Disclaimer
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                PaperLab uses artificial intelligence to provide marking and feedback.
                Please be aware of the following:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>
                  <strong>Not official marking:</strong> Our AI marking is for educational
                  feedback only and does not constitute official exam results
                </li>
                <li>
                  <strong>Potential inaccuracies:</strong> AI systems may occasionally make
                  errors in marking or provide imperfect feedback
                </li>
                <li>
                  <strong>Continuous improvement:</strong> We work to improve accuracy, but
                  results should be used as a learning tool, not definitive assessment
                </li>
                <li>
                  <strong>Subject limitations:</strong> Some subjects or question types may
                  be marked more accurately than others
                </li>
                <li>
                  <strong>No guarantee:</strong> We do not guarantee that using PaperLab will
                  improve exam performance
                </li>
              </ul>
            </section>

            {/* Service Availability */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Service Availability
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                We strive to provide reliable service, but we do not guarantee uninterrupted
                availability. We may modify, suspend, or discontinue any aspect of the service
                at any time without prior notice.
              </p>
            </section>

            {/* Limitation of Liability */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Limitation of Liability
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                To the fullest extent permitted by law, PaperLab and its team shall not be
                liable for any indirect, incidental, special, consequential, or punitive
                damages arising from your use of the service.
              </p>
            </section>

            {/* Changes to Terms */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Changes to These Terms
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                We may update these Terms of Service from time to time. We will notify users
                of significant changes. Your continued use of PaperLab after changes
                constitutes acceptance of the updated terms.
              </p>
            </section>

            {/* Contact */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Contact Us
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                If you have any questions about these Terms of Service, please contact us at:
              </p>
              <p className="mt-4 font-body font-medium text-indigo-deep">
                <a href="mailto:support@mypaperlab.com" className="hover:underline">
                  support@mypaperlab.com
                </a>
              </p>
            </section>
          </div>
        </div>
      </div>
      <Footer />
    </main>
  );
}
