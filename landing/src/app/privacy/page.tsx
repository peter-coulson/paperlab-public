import { Header } from "@/components/sections/Header";
import { Footer } from "@/components/sections/Footer";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy | PaperLab",
  description: "PaperLab privacy policy - how we handle your data",
};

export default function PrivacyPage() {
  return (
    <main>
      <Header variant="solid" />
      <div className="bg-warm-white pt-24 pb-16 md:pt-32 md:pb-24">
        <div className="mx-auto max-w-3xl px-6 lg:px-8">
          <h1 className="font-display text-3xl font-semibold text-text-primary md:text-4xl">
            Privacy Policy
          </h1>
          <p className="mt-4 font-body text-text-secondary">
            Last updated: January 19, 2026
          </p>

          <div className="mt-12 space-y-10">
            {/* Introduction */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Introduction
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                PaperLab (&quot;we&quot;, &quot;our&quot;, or &quot;us&quot;) is committed to protecting your privacy.
                This Privacy Policy explains how we collect, use, and safeguard your information
                when you use our mobile application and services. PaperLab is intended for users
                aged 13 and above.
              </p>
            </section>

            {/* Camera and Photo Library */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Camera and Photo Library Usage
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                PaperLab requires access to your device&apos;s camera and/or photo library to
                photograph exam papers for AI-powered marking. This is the core functionality
                of our service. We only access photos that you explicitly select or capture
                within the app.
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Camera access is used solely to photograph exam papers</li>
                <li>Photo library access allows you to select existing images of exam work</li>
                <li>We do not access or scan photos outside of your explicit selections</li>
                <li>We do not access your camera or photo library in the background</li>
              </ul>
            </section>

            {/* Third-Party AI Processing */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Third-Party AI Processing
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                <strong>Important:</strong> Your exam paper images are sent to third-party AI
                services for processing. To provide automated marking, PaperLab uses AI services
                from <strong>OpenAI</strong>, <strong>Anthropic</strong>, and{" "}
                <strong>Google (Gemini)</strong>.
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Your images are transmitted to these providers for analysis and marking</li>
                <li>This processing is essential for the app to function</li>
                <li>By uploading images, you consent to this data sharing</li>
              </ul>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                <strong>Data retention by AI providers:</strong>
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>
                  <strong>OpenAI:</strong> Retained up to 30 days for abuse monitoring, then deleted
                </li>
                <li>
                  <strong>Anthropic:</strong> Retained 7-30 days for trust and safety, then deleted
                </li>
                <li>
                  <strong>Google (Gemini):</strong> Retained temporarily for processing, then deleted
                </li>
              </ul>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                None of these providers use your API data for model training.
              </p>
            </section>

            {/* Image Storage */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Image Storage
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                Images of exam papers you submit are securely stored on Cloudflare R2,
                a cloud storage service. These images are used to process your marking
                requests and provide feedback.
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Images are transmitted using secure, encrypted connections (HTTPS/TLS)</li>
                <li>Images are retained until you delete them or delete your account</li>
                <li>Data is stored in the United States</li>
              </ul>
            </section>

            {/* Authentication */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Authentication and Account Data
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                We use <strong>Supabase</strong> for authentication services. When you create
                an account, we collect and store:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Your email address</li>
                <li>Encrypted password (for email/password accounts)</li>
                <li>Authentication tokens for secure access</li>
              </ul>
            </section>

            {/* OAuth Providers */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Sign-In with Apple and Google
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                If you choose to sign in using Apple Sign-In or Google Sign-In, authentication
                data is processed by those respective services. We receive limited information:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Your email address (or a relay email for Apple Hide My Email)</li>
                <li>A unique identifier for your account</li>
                <li>Your name (if you choose to share it)</li>
              </ul>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                We do not receive or store your passwords from these services.
              </p>
            </section>

            {/* Data Retention */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Data Retention
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                We retain your data according to the following policies:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>
                  <strong>Uploaded images:</strong> Retained until you delete them or your account
                </li>
                <li>
                  <strong>Account data:</strong> Retained while your account is active
                </li>
                <li>
                  <strong>Marking results:</strong> Stored to provide you with history and progress tracking
                </li>
              </ul>
            </section>

            {/* Analytics */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Analytics and Tracking
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                PaperLab does not track you. We do not use advertising trackers, behavioral
                tracking tools, or share data with advertising networks. We may collect basic
                technical metrics (error logs, crash reports) to improve the app.
              </p>
            </section>

            {/* Third-Party Services */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Third-Party Services
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                We use the following third-party services to operate PaperLab:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>
                  <strong>Supabase:</strong> Authentication and account management
                </li>
                <li>
                  <strong>Cloudflare:</strong> Image storage (R2) and web app hosting (Pages)
                </li>
                <li>
                  <strong>Railway:</strong> Backend application hosting
                </li>
                <li>
                  <strong>OpenAI, Anthropic, Google Gemini:</strong> AI-powered marking
                </li>
                <li>
                  <strong>Google, Apple:</strong> OAuth sign-in services
                </li>
              </ul>
            </section>

            {/* Account Deletion */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Account Deletion
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                You can delete your account and all associated data at any time using the
                &quot;Delete Account&quot; button in the app settings. This action is immediate
                and cannot be undone.
              </p>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                Alternatively, you can contact us to request manual deletion:
              </p>
              <p className="mt-4 font-body font-medium text-indigo-deep">
                <a href="mailto:support@mypaperlab.com" className="hover:underline">
                  support@mypaperlab.com
                </a>
              </p>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                When your account is deleted, your data is removed immediately. Backups may
                retain data for up to 90 days for disaster recovery, after which it is
                permanently purged.
              </p>
            </section>

            {/* Your Rights */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Your Rights
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                You have the right to:
              </p>
              <ul className="mt-4 list-disc pl-6 font-body text-text-secondary space-y-2">
                <li>Access a copy of your personal data</li>
                <li>Request correction of inaccurate data</li>
                <li>Request deletion of your account and data</li>
                <li>Request your data in a portable format</li>
              </ul>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                If you are in the EEA or California, you may have additional rights under
                GDPR/CCPA. Contact us to exercise these rights.
              </p>
            </section>

            {/* Contact */}
            <section>
              <h2 className="font-display text-xl font-semibold text-text-primary md:text-2xl">
                Contact Us
              </h2>
              <p className="mt-4 font-body text-text-secondary leading-relaxed">
                If you have any questions about this Privacy Policy, please contact us at:
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
