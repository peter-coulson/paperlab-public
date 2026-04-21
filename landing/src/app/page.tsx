import { Header } from "@/components/sections/Header";
import { Hero } from "@/components/sections/Hero";
import { Solution } from "@/components/sections/Solution";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { Differentiator } from "@/components/sections/Differentiator";
import Scope from "@/components/sections/Scope";
import { CTA } from "@/components/sections/CTA";
import { Footer } from "@/components/sections/Footer";

export default function Home() {
  return (
    <main>
      <Header />
      <Hero />
      <Solution />
      <HowItWorks />
      <Differentiator />
      <Scope />
      <CTA />
      <Footer />
    </main>
  );
}
