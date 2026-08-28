FROM python:3.10-alpine AS build
ENV HOME=/app
WORKDIR $HOME
RUN apk add --no-cache --virtual build-dependencies git build-base
COPY requirements.txt ./
RUN pip3 install -r requirements.txt


FROM python:3.10-alpine
LABEL org.opencontainers.image.authors="Nils Ost"
ENV HOME=/app
WORKDIR $HOME
COPY --from=build /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY . .
EXPOSE 8000/tcp 8001/tcp
ENTRYPOINT ["python3"]
CMD ["main.py"]
