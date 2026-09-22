# 1D Dittus–Boelter project

Learning project: use Python to explore how the **Dittus–Boelter** correlation describes convective heat transfer for turbulent flow in a smooth tube, and how changing fluid velocity changes cooling performance.

## Why this exists

I am a mechanical engineering student. This repo is practice in translating a textbook correlation into code, plots, and a clear engineering narrative — the same habit I want on internship analysis work.

## What the correlation is doing (plain language)

Dittus–Boelter relates Nusselt number to Reynolds and Prandtl numbers for heating/cooling in pipes. Practically: it helps estimate how much heat transfer you get as flow speed (and therefore Re) changes.

## How to run

```bash
# from repo root (adjust if your entrypoint differs)
python3 -m pip install -r requirements.txt  # if present
python3 main.py  # or the actual script name in this repo
```

## Results

Add 1–2 plots here (Nu vs Re, or heat-transfer coefficient vs velocity) and a one-paragraph interpretation.

## Non-goals

- Not a production heat-exchanger design tool
- Not validated against lab data yet

## Author

Barrett Lemons — [barrettlemons.com](https://barrettlemons.com)
