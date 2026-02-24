# Fitbit AI Health Coach

This is a follow-up to [fitbit_analytics](https://github.com/hamza-menay/fitbit_analytics), which I built earlier. That version was in French and focused purely on visualization. This one adds AI coaching and switches to English.

I built the first version because I was tired of the Fitbit app showing me daily averages when I wanted to see the actual data. Every heartbeat, every step, every sleep stage, second by second. This version keeps all of that and adds an AI coach that can look at your data and answer questions about it.

## What it does

- **Continuous data visualization**: See every data point instead of daily summaries
- **Multiple metrics**: Heart rate, sleep stages, SpO2, HRV, steps, stress scores
- **Interactive charts**: Zoom, pan, explore with Plotly
- **PDF reports**: Generate printable health reports
- **AI coaching**: Ask questions about your data (requires Gemini API key)
- **Local only**: Your data never leaves your machine

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

## What's new vs fitbit_analytics

| Feature | fitbit_analytics | fitbit-ai-coach (this) |
|---------|------------------|------------------------|
| Language | French | English |
| AI coaching | No | Yes (Gemini) |
| PDF export | Yes | Yes |
| Continuous charts | Yes | Yes |

## Why I made this

The Fitbit app aggregates everything into daily summaries. I wanted to see heart rate variability during specific activities, sleep patterns across full time ranges, how different metrics correlate at specific moments, and raw data I could export for my own records.

## Privacy

- No data is stored on any server
- Everything processes locally in your browser
- The AI coach only sends data to Gemini if you provide an API key and explicitly ask a question

## Requirements

- Python 3.8+
- See `requirements.txt` for packages

## License

MIT
