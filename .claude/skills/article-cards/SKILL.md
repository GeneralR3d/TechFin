---
name: implement-article-cards
description: Use when trying to implement article cards on events page
---
You are given a task to integrate an existing React component in the codebase

The codebase should support:
- shadcn project structure  
- Tailwind CSS
- Typescript

If it doesn't, provide instructions on how to setup project via shadcn CLI, install Tailwind or Typescript.

Determine the default path for components and styles. 
If default path for components is not /components/ui, provide instructions on why it's important to create this folder
Copy-paste this component to /components/ui folder:
```tsx
article-cards.tsx
import React from 'react';
import { cn } from '@/lib/utils'; // Assuming you have a clsx/tailwind-merge utility

/**
 * Props for the ArticleCard component.
 */
interface ArticleCardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** The category of the article (e.g., 'FOOD', 'ARCHITECTURE'). */
  category: string;
  /** The main title of the article. */
  title: string;
  /** The price to read the article. */
  price: number;
  /** The URL for the background image. */
  imageUrl: string;
  /** The gradient classes for the overlay, e.g., 'from-cyan-500 to-blue-500'. */
  gradient: string;
}

export const ArticleCard = React.forwardRef<HTMLDivElement, ArticleCardProps>(
  ({ category, title, price, imageUrl, gradient, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'group relative flex h-80 cursor-pointer flex-col justify-between overflow-hidden rounded-xl bg-cover bg-center p-6 text-white shadow-lg transition-all duration-300 ease-in-out hover:-translate-y-1 hover:scale-105 hover:shadow-2xl',
          className
        )}
        style={{ backgroundImage: `url(${imageUrl})` }}
        {...props}
      >
        {/* Gradient Overlay */}
        <div
          className={cn(
            'absolute inset-0 bg-gradient-to-t opacity-70 transition-opacity duration-300 group-hover:opacity-80',
            gradient
          )}
        />
        
        {/* Content Container */}
        <div className="relative z-10 flex h-full flex-col justify-between">
          {/* Top Section: Category */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest opacity-80">
              {category}
            </p>
            <h2 className="text-2xl font-bold">{title}</h2>
          </div>
          
          {/* Bottom Section: Read Button */}
          <div className="self-start">
            <span
              className={cn(
                'rounded-md bg-white/20 px-4 py-2 text-sm font-semibold backdrop-blur-sm transition-all duration-300 group-hover:bg-white/30'
              )}
            >
              Read for ${price.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    );
  }
);

ArticleCard.displayName = 'ArticleCard';

demo.tsx
import { ArticleCard } from '@/components/ui/article-cards'; // Adjust the import path

const articles = [
  {
    category: 'FOOD',
    title: 'Wake Up and Smell the Coffee',
    price: 0.99,
    imageUrl: 'https://www.thiings.co/_next/image?url=https%3A%2F%2Flftz25oez4aqbxpq.public.blob.vercel-storage.com%2Fimage-shBKuu4CZPoxpdoQH7r6Xn5jcZlCRq.png&w=320&q=75',
    gradient: 'from-emerald-400/70 to-teal-600/70',
  },
  {
    category: 'ARCHITECTURE',
    title: 'The Brand New NASA Office',
    price: 0.19,
    imageUrl: 'https://www.thiings.co/_next/image?url=https%3A%2F%2Flftz25oez4aqbxpq.public.blob.vercel-storage.com%2Fimage-2kErHQIkqMuToUFqQ4XSMhya9d6NqZ.png&w=320&q=75',
    gradient: 'from-slate-800/70 to-slate-900/70',
  },
  {
    category: 'TRAVEL',
    title: 'Experience the Saharan Sands',
    price: 2.29,
    imageUrl: 'https://www.thiings.co/_next/image?url=https%3A%2F%2Flftz25oez4aqbxpq.public.blob.vercel-storage.com%2Fimage-5FKJfLGlXSNveVVEHP0G4l2qyXGuLF.png&w=320&q=75',
    gradient: 'from-amber-400/70 to-orange-600/70',
  },
  {
    category: 'INTERIOR',
    title: '9 Air-Cleaning Plants Your Home Needs',
    price: 0.09,
    imageUrl: 'https://www.thiings.co/_next/image?url=https%3A%2F%2Flftz25oez4aqbxpq.public.blob.vercel-storage.com%2Fimage-2lorEIIaeeDsHDW0gQw4MbmuyVqwXH.png&w=320&q=75',
    gradient: 'from-sky-300/70 to-cyan-400/70',
  },
  {
    category: 'FOOD',
    title: 'One Month Sugar Detox',
    price: 0.99,
    imageUrl: 'https://www.thiings.co/_next/image?url=https%3A%2F%2Flftz25oez4aqbxpq.public.blob.vercel-storage.com%2Fimage-5RC9cCQElsr5G9D6fw15rohV86HSp0.png&w=320&q=75',
    gradient: 'from-rose-400/70 to-red-500/70',
  },
  {
    category: 'PHOTOGRAPHY',
    title: 'Shooting Minimal Instagram Photos',
    price: 0.29,
    imageUrl: 'https://www.thiings.co/_next/image?url=https%3A%2F%2Flftz25oez4aqbxpq.public.blob.vercel-storage.com%2Fimage-qzcaGMjbD8jUVkF6Pr2zNhONiA3NCZ.png&w=320&q=75',
    gradient: 'from-blue-400/70 to-indigo-500/70',
  },
];

export default function ArticleCardGridDemo() {
  return (
    <div className="p-4 md:p-8 bg-background">
        <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground">Lifestyle.</h1>
            <p className="text-muted-foreground">The latest and best lifestyle articles selected by our editorial office.</p>
        </div>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3">
        {articles.map((article, index) => (
          <ArticleCard
            key={index}
            category={article.category}
            title={article.title}
            price={article.price}
            imageUrl={article.imageUrl}
            gradient={article.gradient}
          />
        ))}
      </div>
    </div>
  );
}
```

Implementation Guidelines
 1. Analyze the component structure and identify all required dependencies
 2. Review the component's argumens and state
 3. Identify any required context providers or hooks and install them
 4. Questions to Ask
 - What data/props will be passed to this component?
 - Are there any specific state management requirements?
 - Are there any required assets (images, icons, etc.)?
 - What is the expected responsive behavior?
 - What is the best place to use this component in the app?

Steps to integrate
 0. Copy paste all the code above in the correct directories
 1. Install external dependencies
 2. Fill image assets with Unsplash stock images you know exist
 3. Use lucide-react icons for svgs or logos if component requires them
