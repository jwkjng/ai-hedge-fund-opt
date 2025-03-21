# AI Hedge Fund (Fork)

This is a fork of the original [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) project, optimized for use with the Polygon.io API. The goal of this project is to explore the use of AI to make trading decisions. This project is for **educational** purposes only and is not intended for real trading or investment.

This system employs several agents working together:

1. Ben Graham Agent - The godfather of value investing, only buys hidden gems with a margin of safety
2. Bill Ackman Agent - An activist investors, takes bold positions and pushes for change
3. Warren Buffett Agent - The oracle of Omaha, seeks wonderful companies at a fair price
4. Fundamentals Agent - Analyzes fundamental data and generates trading signals
5. Sentiment Agent - Analyzes market sentiment and generates trading signals
6. Risk Manager - Calculates risk metrics and sets position limits

<img width="1020" alt="Screenshot 2025-03-08 at 4 45 22 PM" src="https://github.com/user-attachments/assets/d8ab891e-a083-4fed-b514-ccc9322a3e57" />

**Note**: the system simulates trading decisions, it does not actually trade.

## Disclaimer

This project is for **educational and research purposes only**.

- Not intended for real trading or investment
- No warranties or guarantees provided
- Past performance does not indicate future results
- Creator assumes no liability for financial losses
- Consult a financial advisor for investment decisions

By using this software, you agree to use it solely for learning purposes.

## Table of Contents

- [Setup](#setup)
- [Usage](#usage)
  - [Running the Hedge Fund](#running-the-hedge-fund)
  - [Running the Backtester](#running-the-backtester)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [Feature Requests](#feature-requests)
- [License](#license)

## Setup

Clone the repository:

```bash
git clone https://github.com/yourusername/ai-hedge-fund-opt.git
cd ai-hedge-fund-opt
```

1. Install Poetry (if not already installed):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:

```bash
poetry install
```

3. Set up your environment variables:

```bash
# Create .env file for your API keys
cp .env.example .env
```

4. Set your API keys:

```bash
# For running LLMs hosted by openai (gpt-4o, gpt-4o-mini, etc.)
# Get your OpenAI API key from https://platform.openai.com/
OPENAI_API_KEY=your-openai-api-key

# For running LLMs hosted by groq (deepseek, llama3, etc.)
# Get your Groq API key from https://groq.com/
GROQ_API_KEY=your-groq-api-key

# For getting financial data to power the hedge fund
# Get your Polygon.io API key from https://polygon.io/
POLYGON_API_KEY=your-polygon-api-key
```

**Important**: You must set `OPENAI_API_KEY`, `GROQ_API_KEY`, or `DEEPSEEK_API_KEY` for the hedge fund to work. If you want to use LLMs from all providers, you will need to set all API keys.

To access financial data, you will need to set the `POLYGON_API_KEY` in the .env file. You can get a free API key from [Polygon.io](https://polygon.io/) which includes:

- Real-time and historical stock prices
- Company financials and metrics
- News and market data

Note: The free tier has rate limits. For production use, consider upgrading to a paid plan.

## Usage

### Running the Hedge Fund

```bash
poetry run python src/main.py --ticker ZG,TSLA,ANGI
```

**Example Output:**
```json
{
  "fundamentals": {
    "ZG": {
      "signal": "neutral",
      "confidence": 0.7,
      "reasoning": "Negative net margin of -6.2%\nStrong current ratio of 3.1",
      "metrics": {
        "score": -0.1,
        "net_margin": -0.062,
        "current_ratio": 3.125
      }
    }
  },
  "warren_buffett": {
    "ZG": {
      "signal": "neutral",
      "confidence": 0.8,
      "reasoning": "Weak ROE of -2.9%\nWeak operating margin of -10.8%\nLow debt-to-equity ratio of 0.3",
      "metrics": {
        "score": -0.2,
        "roe": -0.029,
        "operating_margin": -0.108,
        "debt_to_equity": 0.323
      }
    }
  },
  "sentiment": {
    "ZG": {
      "signal": "neutral",
      "confidence": 0.7,
      "reasoning": "News sentiment: negative based on 2 recent articles",
      "metrics": {
        "news_score": -0.5,
        "total_score": -0.5
      }
    }
  },
  "risk_manager": {
    "ZG": {
      "signal": "bearish",
      "confidence": 0.8,
      "reasoning": "Risk Level: HIGH\nAnnual Volatility: 51.5%\nRecommended Position Size: $50,000\nStop Loss Level: 51.5%",
      "metrics": {
        "volatility": 0.515,
        "position_size": 50000.0,
        "stop_loss": 0.515,
        "risk_level": "high"
      }
    }
  }
}
```

You can also specify a `--show-reasoning` flag to print the reasoning of each agent to the console.

```bash
poetry run python src/main.py --ticker ZG,TSLA,ANGI --show-reasoning
```

You can optionally specify the start and end dates to make decisions for a specific time period.

```bash
poetry run python src/main.py --ticker ZG,TSLA,ANGI --start-date 2024-01-01 --end-date 2024-03-01 
```

### Running the Backtester

```bash
poetry run python src/backtester.py --ticker ZG,TSLA,ANGI
```

You can optionally specify the start and end dates to backtest over a specific time period.

```bash
poetry run python src/backtester.py --ticker ZG,TSLA,ANGI --start-date 2024-01-01 --end-date 2024-03-01
```

## Project Structure

```
ai-hedge-fund-opt/
├── src/
│   ├── agents/                   # Agent definitions and workflow
│   │   ├── fundamentals.py       # Fundamental analysis agent
│   │   ├── portfolio_manager.py  # Portfolio management agent
│   │   ├── risk_manager.py       # Risk management agent
│   │   ├── sentiment.py          # Sentiment analysis agent
│   │   ├── warren_buffett.py     # Warren Buffett agent
│   ├── tools/                    # Agent tools
│   │   ├── polygon_api.py        # Polygon.io API integration
│   ├── backtester.py             # Backtesting tools
│   ├── main.py                   # Main entry point
├── pyproject.toml
├── ...
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

**Important**: Please keep your pull requests small and focused. This will make it easier to review and merge.

## Feature Requests

If you have a feature request, please open an [issue](https://github.com/yourusername/ai-hedge-fund-opt/issues) and make sure it is tagged with `enhancement`.

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
