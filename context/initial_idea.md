Dashboard

Event: Iran war
Yahoo news: Iran war is tragic! <links>
Reddit: Buy OILL <links>
Linkedin: US is going down <links>



Events: Japan yen crisis
Yahoo:  <links>
 <links>
 <links>


Sectors News -> different sector specific news, aggregate from source
Sector heatmap (similar to below) -> news sentiment/hot or cooling sectors
	

Of all news today, display the whole knowledge graph 

Frontend: Dashboard data to pull from
Events, news: Come from Backend graph, can link to actual news source
Market data: directly connect via API, alphavantage, coinghecko
Perform data analytics: count of how many articles per event -> heatmap
Each new “news”, analysis portion:
Sentiment of diff sector
Possible risks (or implications)
Potential development
Backend: 
Agent to scrape data + links + sentiment output (bullish or bearish)
Sentiment for event: +ve or -ve
Sentiment for stock/sector: bullish or bearish. Oil TO THE MOON. SaaS dead.
API endpoints for the frontend to fetch the data fro



Datapipeline
Ingest the news from different sources
Yahoo finance (Jayce)
Reddit (Jden)
https://site.financialmodelingprep.com/developer/docs#Stock-News | Alphavantage 
https://github.com/Jigisha-p/Automated-Financial-News-Scraping-and-Structured-Data-Conversion/blob/master/4.Automate_Scrapping.ipynb (Shianne)


Draw relation between news
Simulated Internal Data: e.g., the 2023 banking crisis, 2024 rate cuts in PDF forms
Old chats needs to be “summarised” (not important)

— —

Prompts (steps)
Look at this piece of news, here are all the current “events” i have: find if this piece fits into any current one.
If not, create a new “event”
Based on this piece of news: identify the sectors affected. For each sector, think about whether it affects it bullishly or bearishly

Prompts (per event, each with many articles) -> run once every few hours
Look at all the new articles in this bucket. Based on the new articles received, analyze the most recent development and suggest possible risks in future.
Hey there is war! I predict gold will go up. Buy gold.


Sectors
Tech
Consumer discretionary/cyclical
Medical
Energy
Defence
Financial services
Healthcare industrials
etc…..


Building the Knowledge Graph is arguably the most impressive part of this hackathon project. Relational databases (SQL) are terrible at finding 2nd and 3rd-order consequences, but a Graph Database thrives on it. It is the perfect tool to map out the butterfly effect of macroeconomics.
To build this effectively, you need to define a strict Ontology (your schema of nodes and edges) and then set up an automated extraction pipeline.
Here is exactly how you should structure and build it.

1. The Ontology: What Nodes and Edges to Use
If you let an LLM extract nodes freely, you will end up with a messy, disconnected graph (e.g., one node called "US", another called "United States", another called "USA"). You must constrain the AI to specific node labels and relationship types.
Core Node Categories (Labels)
Tag your knowledge base with these primary node types:
MacroTheme: The overarching narrative. (e.g., Disinflation, AI CapEx, Middle East Tensions, Trade War)
Event: Specific occurrences driving the news. (e.g., Fed Rate Hike, NFP Miss, CPI Print, Port Strike)
Indicator: The quantitative metric being discussed. (e.g., US CPI, Brent Crude Price, 10-Year Treasury Yield)
AssetClass: The financial instruments affected. (e.g., US Equities, Emerging Market FX, High Yield Bonds, Gold)
Geography / Region: Where it's happening. (e.g., United States, Eurozone, China, LATAM)
Institution: The key players. (e.g., Federal Reserve, Bank of Japan, OPEC, US Treasury)
Core Relationships (Edges)
The edges are the secret sauce. They map out the risk implications. Force your AI to use only these directional verbs:
INCREASES_RISK_OF (e.g., High Inflation $\rightarrow$ INCREASES_RISK_OF $\rightarrow$ Fed Rate Hike)
DRIVES_UP / DRIVES_DOWN (e.g., Fed Rate Hike $\rightarrow$ DRIVES_DOWN $\rightarrow$ Tech Equities)
CORRELATED_WITH (e.g., USD Strength $\rightarrow$ CORRELATED_WITH $\rightarrow$ Gold Weakness)
PART_OF_THEME (e.g., CPI Print $\rightarrow$ PART_OF_THEME $\rightarrow$ Disinflation)
Node Properties (Metadata)
Inside each node or edge, store metadata to power your frontend filters:
sentiment_score: Float (-1.0 to 1.0)
timestamp: When the relationship was established
source_url: Link to the news article or research note that proved this link (crucial for the "Intuitive Dashboard" requirement).

2. How to Build It (The Technical Pipeline)
Since you are building a modern, high-performance web app, a backend stack utilizing Python and FastAPI is the perfect fit here to handle the AI orchestration and database routing.
Step 1: Set up Neo4j
For a hackathon, don't waste time deploying databases locally. Spin up a free Neo4j AuraDB cloud instance. It gives you connection credentials out of the box that play perfectly with Python. If you want to deploy the whole backend later, you can easily containerize the FastAPI app and throw it on Google Cloud Run.
Step 2: The LLM Extraction Pipeline (LangChain)
When your FastAPI backend ingests a news article, pass the text to an LLM. You can use LangChain's LLMGraphTransformer. You explicitly pass your defined ontology (the nodes and edges listed above) into the transformer.
The LLM will read the text: "The unexpected surge in US CPI today means the Federal Reserve is highly likely to hike rates next month, which will hammer tech stocks." ...and automatically output structured JSON representing the nodes (US CPI, Federal Reserve, Tech Stocks) and the edges linking them.
Step 3: Ingestion via Cypher
Once the LLM formats the data, you use the Neo4j Python driver to push it into the database using Cypher (Neo4j's query language).
Step 4: Querying for "Risk Implications" (The Bonus Feature)
When a user clicks on "US CPI" on the frontend, your backend runs a Cypher query to find the chain reaction. It looks something like this:
Cypher
MATCH path = (startNode:Indicator {name: "US CPI"})-[*1..3]->(impactedAsset:AssetClass)
RETURN path


This single query instantly traverses up to 3 degrees of separation, effectively generating your automated risk scenario: US CPI $\rightarrow$ Fed Hike $\rightarrow$ Rates Volatility.

3. Frontend Visualization
To display this in your React/Next.js frontend, use React Flow. It allows you to build a highly interactive, drag-and-drop canvas. Your FastAPI backend simply queries Neo4j, formats the nodes and edges into a standard JSON array, and sends it to the frontend where React Flow renders the network.
Would you like me to write out a quick Python/FastAPI code snippet showing exactly how to use LangChain to extract these specific macro nodes from a piece of text?




ALL INDUSTRIES

Industry List
Biotechnology
Banks - Regional
Shell Companies
Software - Application
Software - Infrastructure
Medical Devices
Asset Management
Capital Markets
Drug Manufacturers - Specialty & Generic
Aerospace & Defense
Oil & Gas Exploration & Production
Specialty Industrial Machinery
Internet Content & Information
Information Technology Services
Semiconductors
Packaged Foods
Specialty Chemicals
Medical Instruments & Supplies
Oil & Gas Midstream
Auto Parts
Engineering & Construction
Credit Services
Restaurants
Telecom Services
Medical Care Facilities
Diagnostics & Research
Gold
Specialty Retail
Oil & Gas Equipment & Services
Entertainment
Electronic Components
Health Information Services
Electrical Equipment & Parts
Other Industrial Metals & Mining
Specialty Business Services
Insurance - Property & Casualty
Communication Equipment
Real Estate Services
Education & Training Services
Utilities - Regulated Electric
REIT - Mortgage
Advertising Agencies
Computer Hardware
Internet Retail
Marine Shipping
Building Products & Equipment
Furnishings, Fixtures & Appliances
Leisure
Scientific & Technical Instruments
Household & Personal Products
Apparel Retail
Integrated Freight & Logistics
Semiconductor Equipment & Materials
Auto Manufacturers
Auto & Truck Dealerships
REIT - Retail
Farm & Heavy Construction Machinery
Conglomerates
Consulting Services
Packaging & Containers
Apparel Manufacturing
Insurance Brokers
Industrial Distribution
Solar
Steel
Security & Protection Services
Rental & Leasing Services
Utilities - Renewable
Electronic Gaming & Multimedia
Drug Manufacturers - General
Farm Products
REIT - Residential
REIT - Office
Residential Construction
Waste Management
Insurance - Life
Travel Services
Oil & Gas Refining & Marketing
Banks - Diversified
Oil & Gas Integrated
Airlines
Consumer Electronics
Chemicals
Pollution & Treatment Controls
REIT - Healthcare Facilities
Beverages - Non-Alcoholic
Staffing & Employment Services
Resorts & Casinos
Insurance - Specialty
REIT - Specialty
Metal Fabrication
REIT - Industrial
Trucking
Utilities - Regulated Gas
Recreational Vehicles
Building Materials
REIT - Diversified
Real Estate - Development
REIT - Hotel & Motel
Footwear & Accessories
Other Precious Metals & Mining
Financial Data & Stock Exchanges
Broadcasting
Personal Services
Uranium
Food Distribution
Utilities - Regulated Water
Mortgage Finance
Gambling
Medical Distribution
Lodging
Agricultural Inputs
Railroads
Insurance - Diversified
Grocery Stores
Healthcare Plans
Luxury Goods
Tobacco
Beverages - Wineries & Distilleries
Tools & Accessories
Discount Stores
Oil & Gas Drilling
Utilities - Independent Power Producers
Beverages - Brewers
Utilities - Diversified
Electronics & Computer Distribution
Airports & Air Services
Publishing
Insurance - Reinsurance
Home Improvement Retail
Pharmaceutical Retailers
Coking Coal
Thermal Coal
Lumber & Wood Production
Copper
Financial Conglomerates
Business Equipment & Supplies
Silver
Paper & Paper Products
Confectioners
Aluminum
Textile Manufacturing
Department Stores
Infrastructure Operations
Real Estate - Diversified
