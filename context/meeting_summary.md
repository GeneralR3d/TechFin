News sentiment dashboard pipeline design
Dashboard Design & Structure
News sentiment dashboard with three main sections:
Top section: Event cards with summaries of 3-4 articles plus links
Middle section: Heat map showing event categorization and topic intensity
Bottom section: Knowledge graph with macro indicators (S&P, NASDAQ, Bitcoin)
Heat map tracks 24-hour news volume changes by topic/sector
Shows “hot” vs “cooling” topics based on article frequency
Categorizes by industry sectors for trend analysis
Data Pipeline Architecture
Backend handles data ingestion and processing
Separate scraper jobs run independently
Agent processes and categorizes news into event buckets
AI pipeline workflow:
Classify news into existing events or create new event buckets
Analyze sentiment per news article (bullish/bearish by sector)
Generate event-level analysis with risk assessment and predictions
Database structure uses 145 Yahoo Finance industries as classification system
Frontend queries backend via FastAPI, separate from Next.js/React frontend
Data Sources & Technical Implementation
Primary sources identified:
Yahoo Finance (API available)
Alpha Vantage (free tier for core data)
FMP (Financial Modeling Prep) API
Money Control scraping
CoinGecko for crypto data
Market data integration for live indicators
Reddit scraping as additional news source
Sentiment analysis using LLM classification (positive/negative for events, bullish/bearish for sectors)
Next Steps
Data source assignment by Saturday meeting:
jdgoh: Money Control scraping + Reddit
Team member: Yahoo Finance API integration
Research Neo4j graph database implementation for news relationships
Complete data ingestion pipeline before dashboard development
Build chatbot functionality after core dashboard is operational
Saturday AM/PM or Tuesday PM meeting scheduled for progress review
