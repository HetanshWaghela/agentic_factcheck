# Fact-Checking Agent

A modular fact-checking system that analyzes news articles for accuracy and logical fallacies using AI.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your `.env` file with API keys:
```
GEMINI_API_KEY=your_gemini_key_here
SERPER_API_KEY=your_serper_key_here
```

3. Run the fact checker:
```bash
python main.py
```

## Project Structure

```
├── main.py              # Main entry point - run this to start
├── config.py            # Configuration and user input handling
├── fact_checker.py      # Core FactChecker class and analysis logic
├── evidence_search.py   # Evidence searching and source evaluation
├── prompts.py           # All LLM prompt templates
├── utils.py             # Helper functions and formatting
├── fallacies.csv        # Logical fallacies database
├── requirements.txt     # Python dependencies
└── agent.py            # Original monolithic version (backup)
```

## Core Components

### FactChecker Class (`fact_checker.py`)
- Main analysis pipeline
- Extracts claims from articles
- Verifies claims with external evidence
- Runs parallel processing for speed
- Generates ethics analysis

### EvidenceSearcher Class (`evidence_search.py`) 
- Searches for evidence supporting/refuting claims
- Evaluates source credibility (tier 1-3 ranking)
- Loads full article content for better analysis
- Handles rate limiting and error recovery

### Configuration (`config.py`)
- Manages API keys and environment setup
- Handles user input collection
- Defines credible source lists
- Sets processing parameters

## Key Features

- **Parallel Processing**: Analyzes multiple claims simultaneously
- **Source Credibility**: Ranks sources by reliability (Reuters/AP = tier 1, CNN/NYT = tier 2, etc.)
- **Full Content Analysis**: Loads complete articles instead of just snippets
- **Fallacy Detection**: Identifies logical fallacies using curated database
- **Confidence Scoring**: Provides reliability scores for each claim

## For Backend Developers

To integrate as an API:
1. Import `FactChecker` class from `fact_checker.py`
2. Use `analyze_article()` method for single articles
3. Parse results from the returned dictionary
4. Handle errors with try/catch around the analysis calls

## For Frontend Developers

Expected data flow:
1. **Input**: Article URL + analysis parameters
2. **Output**: JSON with verified claims, verdicts, confidence scores
3. **Progress**: Real-time status updates during analysis
4. **Results**: Formatted report with evidence and fallacy detection

## Customization

- **Prompts**: Modify templates in `prompts.py`
- **Sources**: Update credible source lists in `config.py`  
- **Processing**: Adjust batch sizes and threading in `config.py`
- **Display**: Change result formatting in `utils.py`

## Dependencies

- `langchain` - LLM orchestration
- `langchain-google-genai` - Gemini API integration
- `langchain-community` - Web loading and search
- `pandas` - Data processing
- `python-dotenv` - Environment management
