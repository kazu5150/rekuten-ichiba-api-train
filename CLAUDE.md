# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a simple Python application that provides a command-line interface for searching products on Rakuten Marketplace using the Rakuten Ichiba Item Search API.

## Development Commands

### Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Make sure virtual environment is activated
python rakuten_search.py
```

## Architecture

The project consists of a single Python file with one main class:

- **`RakutenSearchAPI`** (rakuten_search.py): Handles API communication with Rakuten
  - `search_items()`: Performs keyword-based product searches
  - `display_results()`: Formats and displays search results
  
The `main()` function serves as the entry point, handling user input and orchestrating the search flow.

## Important Notes

1. **API Key Configuration**: The Rakuten API application ID is now managed through environment variables:
   - Copy `.env.example` to `.env`
   - Set `RAKUTEN_APP_ID` in the `.env` file
   - The application uses `python-dotenv` to load environment variables

2. **Language**: Documentation and code comments are in Japanese, while the code itself uses English naming conventions.

3. **No Testing Framework**: This project currently has no test suite. When adding tests, you'll need to set up a testing framework first.

4. **No Linting Setup**: There are no code quality tools configured. Consider adding flake8 or pylint configuration if code quality checks are needed.

5. **Security**: The `.env` file containing API keys is excluded from version control via `.gitignore`

## API Integration

The application uses the Rakuten Ichiba Item Search API v20220601 with the following endpoint:
- Base URL: `https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601`
- Requires: Application ID (obtained from Rakuten Developers)
- Returns: Top 5 products matching the search keyword by default