import type { Metadata } from "next";
import Link from "next/link";
import { Radio, Rss, Search, MessageSquare } from "lucide-react";
import "./globals.css";

export const metadata: Metadata = {
  title: "PodListener",
  description: "Podcast social listening for marketers",
};

const navItems = [
  { href: "/", label: "Dashboard", icon: Radio },
  { href: "/feeds", label: "Feeds", icon: Rss },
  { href: "/keywords", label: "Keywords", icon: Search },
  { href: "/mentions", label: "Mentions", icon: MessageSquare },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen">
        <div className="flex min-h-screen">
          <aside className="w-56 bg-gray-900 text-white flex flex-col">
            <div className="p-4 border-b border-gray-700">
              <h1 className="text-lg font-bold flex items-center gap-2">
                <Radio className="w-5 h-5" />
                PodListener
              </h1>
            </div>
            <nav className="flex-1 p-3 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-gray-800 text-sm transition-colors"
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="flex-1 p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
