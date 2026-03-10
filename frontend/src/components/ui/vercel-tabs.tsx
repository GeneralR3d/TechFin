"use client";

import * as React from "react";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

interface Tab {
  id: string;
  label: string;
}

interface VercelTabsProps extends React.HTMLAttributes<HTMLDivElement> {
  tabs: Tab[];
  activeTab?: string;
  onTabChange?: (tabId: string) => void;
}

const VercelTabs = React.forwardRef<HTMLDivElement, VercelTabsProps>(
  ({ className, tabs, activeTab, onTabChange, ...props }, ref) => {
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
    const [activeIndex, setActiveIndex] = useState(0);
    const [hoverStyle, setHoverStyle] = useState({});
    const [activeStyle, setActiveStyle] = useState({ left: "0px", width: "0px" });
    const tabRefs = useRef<(HTMLDivElement | null)[]>([]);

    useEffect(() => {
      if (activeTab) {
        const idx = tabs.findIndex((t) => t.id === activeTab);
        if (idx >= 0) setActiveIndex(idx);
      }
    }, [activeTab, tabs]);

    useEffect(() => {
      if (hoveredIndex !== null) {
        const el = tabRefs.current[hoveredIndex];
        if (el) {
          setHoverStyle({ left: `${el.offsetLeft}px`, width: `${el.offsetWidth}px` });
        }
      }
    }, [hoveredIndex]);

    useEffect(() => {
      const el = tabRefs.current[activeIndex];
      if (el) {
        setActiveStyle({ left: `${el.offsetLeft}px`, width: `${el.offsetWidth}px` });
      }
    }, [activeIndex]);

    useEffect(() => {
      requestAnimationFrame(() => {
        const el = tabRefs.current[0];
        if (el) {
          setActiveStyle({ left: `${el.offsetLeft}px`, width: `${el.offsetWidth}px` });
        }
      });
    }, []);

    return (
      <div ref={ref} className={cn("relative", className)} {...props}>
        <div className="relative">
          {/* Hover highlight */}
          <div
            className="absolute h-[30px] transition-all duration-300 ease-out bg-[#0e0f1114] dark:bg-[#ffffff1a] rounded-[6px]"
            style={{ ...hoverStyle, opacity: hoveredIndex !== null ? 1 : 0 }}
          />
          {/* Active underline */}
          <div
            className="absolute bottom-[-6px] h-[2px] bg-[#0e0f11] dark:bg-white transition-all duration-300 ease-out"
            style={activeStyle}
          />
          {/* Tabs */}
          <div className="relative flex space-x-[6px] items-center">
            {tabs.map((tab, index) => (
              <div
                key={tab.id}
                ref={(el) => { tabRefs.current[index] = el; }}
                className={cn(
                  "px-3 py-2 cursor-pointer transition-colors duration-300 h-[30px]",
                  index === activeIndex
                    ? "text-[#0e0e10] dark:text-white"
                    : "text-[#0e0f1199] dark:text-[#ffffff99]"
                )}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                onClick={() => {
                  setActiveIndex(index);
                  onTabChange?.(tab.id);
                }}
              >
                <div className="text-sm font-medium leading-5 whitespace-nowrap flex items-center justify-center h-full">
                  {tab.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }
);

VercelTabs.displayName = "VercelTabs";

export { VercelTabs };
export type { Tab };
