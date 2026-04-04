FROM ubuntu:latest
LABEL authors="peter"

ENTRYPOINT ["top", "-b"]