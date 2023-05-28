FROM python:3.9-slim

ENV PATH_R2N "/usr/local/r2n"

# Install dependencies
RUN apt-get update && apt-get install -y cron
RUN pip install -r requirements.txt

# Add the Python script
RUN mkdir -p /usr/local/r2n/
RUN mkdir -p /usr/local/r2n/resources

COPY transcript_summarizer.py /usr/local/r2n/
COPY transcript_manager.py /usr/local/r2n/


RUN chmod +x /usr/local/r2n/transcript_summarizer.py
RUN chmod +x /usr/local/r2n/transcript_manager.py

ENTRYPOINT [ "python" ]
CMD [ "/usr/local/r2n/transcript_summarizer.py" ]