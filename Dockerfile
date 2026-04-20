FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

COPY config.json ./
COPY user_data/ ./user_data/

EXPOSE 8080

# --- Required env vars (set these per Railway service) ---
ENV STRATEGY=Strategy01
ENV BYBIT_API_KEY=""
ENV BYBIT_API_SECRET=""
# These override config.json credentials via Freqtrade's native env var system
ENV FREQTRADE__API_SERVER__USERNAME="admin"
ENV FREQTRADE__API_SERVER__PASSWORD="changeme"
ENV FREQTRADE__API_SERVER__JWT_SECRET_KEY="changeme"

CMD ["sh", "-c", "freqtrade trade \
     --logfile /freqtrade/user_data/logs/freqtrade.log \
     --db-url sqlite:////freqtrade/user_data/tradesv3.sqlite \
     --config /freqtrade/config.json \
     --strategy ${STRATEGY}"]
