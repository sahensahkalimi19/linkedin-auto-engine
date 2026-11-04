name: Autonomous LinkedIn Engine

on:
  schedule:
    - cron: '30 3 * * 1,3,5'
  workflow_dispatch:

jobs:
  build-and-post:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          pip install google-genai Pillow playwright requests
          playwright install chromium
          playwright install-deps chromium

      - name: Run LinkedIn Automation Script
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          LINKEDIN_LI_AT: ${{ secrets.LINKEDIN_LI_AT }}
        run: |
          python main.py
