FROM python:3.10-slim

# System update karo aur ffmpeg install karo (video/audio ke liye zaroori hai)
RUN apt-get update && apt-get install -y ffmpeg

# Bot ke liye ek folder banao
WORKDIR /app

# Requirements file copy karo aur libraries install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karo
COPY . .

# Bot ko start karne ki command
CMD ["python", "bot.py"]
