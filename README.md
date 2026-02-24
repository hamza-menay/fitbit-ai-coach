# Fitbit AI Health Coach

I built this because I was tired of the Fitbit app showing me daily averages when I wanted to see the actual data. Every heartbeat, every step, every sleep stage - second by second.

The dashboard runs on Streamlit. You upload your Fitbit Takeout export and get interactive charts you can zoom into. There's also an AI coach (optional, uses Google's Gemini) that looks at your data and answers questions about it.

## What it does

- **Continuous data visualization** - See every data point instead of daily summaries
- **Multiple metrics** - Heart rate, sleep stages, SpO2, HRV, steps, stress scores
- **Interactive charts** - Zoom, pan, explore with Plotly
- **PDF reports** - Generate printable health reports
- **AI coaching** - Ask questions about your data (requires Gemini API key)
- **Local only** - Your data never leaves your machine

## Quick start

1. **Export your Fitbit data:**
   - Go to [Fitbit Data Export](https://www.fitbit.com/settings/data/export)
   - Request your data (takes up to 24 hours)
   - Download the ZIP file

2. **Run the dashboard:**
   ```bash
   pip install -r requirements.txt
   streamlit run health_dashboard.py
   ```

3. **Upload your data:**
   - Upload the `Takeout.zip` file in the sidebar
   - Or place your `Takeout*/Fitbit` folder in the same directory

4. **Optional: Enable AI coaching:**
   - Add your Gemini API key in the sidebar
   - Ask questions about your health patterns

## Why I made this

The Fitbit app aggregates everything into daily summaries. I wanted to see:
- Heart rate variability during specific activities
- Sleep patterns across full time ranges
- How different metrics correlate at specific moments
- Raw data I could export for my own records

## Privacy

- No data is stored on any server
- Everything processes locally in your browser
- The AI coach only sends data to Gemini if you provide an API key and explicitly ask a question

## Requirements

- Python 3.8+
- See `requirements.txt` for packages

## License

MIT
