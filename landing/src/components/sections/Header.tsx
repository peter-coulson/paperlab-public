"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  variant?: "default" | "solid";
}

export function Header({ variant = "default" }: HeaderProps) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const showSolidBackground = variant === "solid" || scrolled;

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        showSolidBackground
          ? "bg-deep-slate/95 backdrop-blur-md shadow-lg"
          : "bg-transparent"
      }`}
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between md:h-20">
          {/* Wordmark */}
          <a href="/" className="group flex items-baseline gap-0">
            <span className="font-display text-xl font-semibold tracking-tight text-text-on-dark md:text-2xl">
              Paper
            </span>
            <span className="font-display text-xl font-semibold tracking-tight text-indigo-light md:text-2xl">
              Lab
            </span>
          </a>

          {/* CTA */}
          <Button
            asChild
            className="rounded-lg bg-indigo-deep px-5 py-2 text-sm font-medium text-white shadow-indigo transition-all hover:bg-indigo-deep/90 hover:shadow-lg md:px-6 md:text-base"
            size="sm"
          >
            <a href="https://app.mypaperlab.com">Try PaperLab</a>
          </Button>
        </div>
      </div>
    </header>
  );
}
