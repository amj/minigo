cgos-image:
	  docker build --build-arg MODEL=${MODEL} --build-arg MODEL_NUM=${MODEL_NUM} -t "gcr.io/tensor-go/cgos-player:${VERSION_TAG}" .

cgos-push: cgos-image
		gcloud docker -- push "gcr.io/tensor-go/cgos-player:${VERSION_TAG}"

.PHONY: cgos-image cgos-push
