import React from "react";
import { cn } from "@/lib/utils";

interface ArticleCardProps extends React.HTMLAttributes<HTMLDivElement> {
  category: string;
  title: string;
  meta?: string;
  imageUrl?: string;
  gradient: string;
  badge?: React.ReactNode;
  footer?: React.ReactNode;
}

export const ArticleCard = React.forwardRef<HTMLDivElement, ArticleCardProps>(
  ({ category, title, meta, imageUrl, gradient, badge, footer, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "group relative flex h-64 cursor-pointer flex-col justify-between overflow-hidden rounded-xl bg-cover bg-center p-5 text-white shadow-lg transition-all duration-300 ease-in-out hover:-translate-y-1 hover:scale-105 hover:shadow-2xl",
          className
        )}
        style={imageUrl ? { backgroundImage: `url(${imageUrl})` } : undefined}
        {...props}
      >
        {/* Gradient Overlay */}
        <div
          className={cn(
            "absolute inset-0 bg-gradient-to-t opacity-90 transition-opacity duration-300 group-hover:opacity-95",
            gradient
          )}
        />

        {/* Content */}
        <div className="relative z-10 flex h-full flex-col justify-between">
          <div>
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-widest opacity-75">
              {category}
            </p>
            <h2 className="text-base font-bold leading-snug line-clamp-3">{title}</h2>
          </div>
          <div>
            <div className="flex items-center justify-between">
              {meta && (
                <span className="text-xs opacity-70">{meta}</span>
              )}
              {badge && <div className="ml-auto">{badge}</div>}
            </div>
            {footer && <div className="mt-1">{footer}</div>}
          </div>
        </div>
      </div>
    );
  }
);

ArticleCard.displayName = "ArticleCard";
