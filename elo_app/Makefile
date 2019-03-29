.PHONY: build push run test static-ip

VERSION = 0.0.4
TAG = gcr.io/sanguine-mark-190003/elo-rating:slack-v$(VERSION)


build:
	docker build . -t $(TAG)

push:
	docker push $(TAG)

run:
	docker run -e ACCESS_KEY='password' -p 5000:5000 --rm $(TAG)

test:
	curl -X POST localhost:5000/player -F "name=tyrone" -H "api-key: password"
	curl -X POST localhost:5000/player -F "name=antonio" -H "api-key: password"
	curl -X GET localhost:5000/player -H "api-key: password"
	curl -X GET localhost:5000/player/tyrone -H "api-key: password"
	curl -X POST localhost:5000/add-result -F "p1_name=tyrone" -F "p2_name=antonio" -F "p1_score=11" -F "p2_score=0" -H "api-key: password"

static-ip:
	gcloud compute addresses create elo-static-ip --global
