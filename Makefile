.PHONY: build push run test

VERSION = 0.0.1
TAG = gcr.io/cognitivebus-playground/elo-rating:slack-v$(VERSION)


build:
	docker build . -t $(TAG)

push:
	docker push $(TAG)

run:
	docker run -p 5000:5000 --rm $(TAG)

test:
	curl -X POST localhost:5000/player -F "name=tyrone" -F "password=password"
	curl -X POST localhost:5000/player -F "name=antonio" -F "password=password"
	curl -X GET localhost:5000/player
	curl -X GET localhost:5000/player/tyrone
	curl -X POST localhost:5000/add-result -F "p1_name=tyrone" -F "p2_name=antonio" -F "p1_score=11" -F "p2_score=0" --user "tyrone:password"
