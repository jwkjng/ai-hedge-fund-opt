# AI Hedge Fund

An AI-powered hedge fund that uses multiple AI agents to analyze stocks and make trading decisions. Each agent represents a different investment strategy or perspective, inspired by famous investors and fundamental analysis techniques.

## Project Structure

```
src/
├── agents/              # AI agents implementing different trading strategies
│   ├── fundamentals.py  # Fundamental analysis agent
│   ├── warren_buffett.py  # Warren Buffett-inspired agent
│   ├── ben_graham.py    # Benjamin Graham-inspired agent
│   ├── bill_ackman.py   # Bill Ackman-inspired agent
│   ├── sentiment.py     # Market sentiment analysis agent
│   └── risk_manager.py  # Risk management agent
├── tools/               # API and utility functions
│   └── api.py          # Financial data API (using Polygon.io)
├── utils/              # Utility functions
│   ├── display.py      # Output formatting utilities
│   └── progress.py     # Progress tracking
├── data/               # Data management
│   └── cache.py        # Caching layer
├── graph/              # State management
│   └── state.py        # Agent state handling
├── main.py            # Main entry point
└── backtester.py      # Backtesting engine

```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-hedge-fund.git
cd ai-hedge-fund
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

Run the analysis for specific stocks:
```bash
poetry run python src/main.py --ticker ZG,TSLA,ANGI
```

Example output:
```
================================================================================
ANALYZING STOCKS FOR 2024-03-20
================================================================================

----------------------------------------
Analyzing ZG...
----------------------------------------

Latest news for ZG:
Date: 2024-03-15
Title: Test Company Reports Strong Q4 Results
Source: Test News
URL: https://example.com/article1

fundamentals Analysis:
Signal: neutral
Confidence: 0.7
Reasoning: Negative net margin of -6.2%
Strong current ratio of 3.1

warren_buffett Analysis:
Signal: neutral
Confidence: 0.8
Reasoning: Weak ROE of -2.9%
Weak operating margin of -10.8%

TRADING DECISIONS
================================================================================
Ticker   Action     Quantity
--------------------------------------------------------------------------------
ZG       hold              0
TSLA     hold              0
ANGI     hold              0

ANALYST SIGNALS
================================================================================
ZG Analysis:
----------------------------------------
Signal Summary: 0 Bullish, 3 Neutral, 3 Bearish
```

## Features

- Multiple AI agents analyzing stocks from different perspectives:
  - Fundamental Analysis
  - Warren Buffett Strategy
  - Benjamin Graham Strategy
  - Bill Ackman Strategy
  - Market Sentiment Analysis
  - Risk Management

- Each agent considers:
  - Financial metrics
  - Market data
  - News sentiment
  - Technical indicators
  - Risk factors

- Aggregated decision making:
  - Weighted voting system
  - Confidence-based position sizing
  - Risk-adjusted returns

## Configuration

The system can be configured through environment variables:

```bash
POLYGON_API_KEY=your_api_key_here
MODEL_PROVIDER=OpenAI  # or other supported providers
MODEL_NAME=gpt-4      # or other models
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Data Sources

The hedge fund uses the following data from Polygon.io:
- Real-time and historical stock prices
- Company financials and metrics
- News and social media sentiment
- Market data and indicators

## Example Output

```json
{
  "sentiment": {
    "AAPL": {
      "signal": "neutral",
      "confidence": 0.7,
      "reasoning": "News sentiment: negative based on 2 recent articles",
      "metrics": {
        "news_score": -0.5,
        "total_score": -0.5
      }
    }
  }
}
```
