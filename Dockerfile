FROM freqtradeorg/freqtrade:stable

# Copy project files
WORKDIR /freqtrade

COPY config.json ./
COPY user_data/ ./user_data/

# Railway injects PORT; FreqUI API server listens on 8080 by default
# (config.json already sets listen_port to 8080)
EXPOSE 8080

# Freqtrade reads secrets from env vars via ${VAR} syntax in config.json
# Required env vars:
#   BINANCE_API_KEY, BINANCE_API_SECRET
#   FREQTRADE_API_USER, FREQTRADE_API_PASS
#   FREQTRADE_JWT_SECRET
#   (optional) TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

CMD ["trade", \
     "--logfile", "/freqtrade/user_data/logs/freqtrade.log", \
     "--db-url", "sqlite:////freqtrade/user_data/tradesv3.sqlite", \
     "--config", "/freqtrade/config.json", \
     "--strategy", "Strategy01"]
