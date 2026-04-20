FROM freqtradeorg/freqtrade:stable

WORKDIR /freqtrade

COPY config.json ./
COPY user_data/ ./user_data/
COPY start.sh ./

EXPOSE 8080

ENV STRATEGY=Strategy01
ENV BYBIT_API_KEY=""
ENV BYBIT_API_SECRET=""
ENV FREQTRADE__API_SERVER__USERNAME="admin"
ENV FREQTRADE__API_SERVER__PASSWORD="changeme"
ENV FREQTRADE__API_SERVER__JWT_SECRET_KEY="changeme"

ENTRYPOINT []
CMD ["/bin/sh", "/freqtrade/start.sh"]
