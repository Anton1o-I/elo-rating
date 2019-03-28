.PHONY: build push run

VERSION = 0.0.1
TAG = gcr.io/cognitivebus-playground/elo-rating:slack-v$(VERSION)


build:
	docker build . -t $(TAG)

push:
	docker push $(TAG)

run:
	docker run -p 5000:5000 --rm $(TAG)
