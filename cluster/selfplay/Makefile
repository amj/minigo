# Version and project can be overridden with the following:
#  make target VERSION_TAG=0.XY PROJECT=foo-project

define staging =
mkdir -p staging
cp ../../*.py staging/
cp ../../requirements.txt staging/
cp player_wrapper.sh staging/
cp tpu_wrapper.sh staging/
endef

tpu-image:
	$(staging)
	docker build -f Dockerfile.tpu -t "gcr.io/$(PROJECT)/minigo-tpu-player:0.1" .
	rm -rfd staging

gpu-image:
	$(staging)
	docker build -f Dockerfile.gpu -t "gcr.io/$(PROJECT)/$(GPU_PLAYER_CONTAINER):$(VERSION_TAG)" .
	rm -rfd staging

py-image:
	$(staging)
	docker build -t "gcr.io/$(PROJECT)/$(CPU_PLAYER_CONTAINER):$(VERSION_TAG)" .
	rm -rfd staging

cc-image:
	docker build -f Dockerfile-cc -t "gcr.io/$(PROJECT)/$(CC_PLAYER_CONTAINER):$(VERSION_TAG)" .

cc-push: cc-image
  gcloud docker -- push "gcr.io/$(PROJECT)/$(CC_PLAYER_CONTAINER):$(VERSION_TAG)"

py-push: py-image
  gcloud docker -- push "gcr.io/$(PROJECT)/$(CPU_PLAYER_CONTAINER):$(VERSION_TAG)"

gpu-push: gpu-image
  gcloud docker -- push "gcr.io/$(PROJECT)/$(GPU_PLAYER_CONTAINER):$(VERSION_TAG)"

tpu-push: tpu-image
  gcloud docker -- push "gcr.io/$(PROJECT)/minigo-tpu-player:0.1"

.PHONY: cc-image cpu-image tpu-image gpu-image image-push cc-push cpu-push gpu-push tpu-push
