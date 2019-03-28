REPO = gcr.io/cognitivebus-playground
NAME = elo-rating
VERSION = latest

build:
	docker build -t $(REPO)/$(NAME):$(VERSION) -f ./Dockerfile .


push:
	gcloud docker -- push $(REPO)/$(NAME):$(VERSION)
