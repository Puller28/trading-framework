FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

COPY config.json ./
COPY user_data/ ./user_data/

EXPOSE 8080

# Set STRATEGY env var per Railway service to select which strategy runs.
# Defaults to Strategy01 if not set.
ENV STRATEGY=Strategy01

CMD ["sh", "-c", "freqtrade trade \
     --logfile /freqtrade/user_data/logs/freqtrade.log \
     --db-url sqlite:////freqtrade/user_data/tradesv3.sqlite \
     --config /freqtrade/config.json \
     --strategy ${STRATEGY}"]
