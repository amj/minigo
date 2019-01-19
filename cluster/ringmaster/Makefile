
gtp:
		mkdir -p staging/cc
		cp ../../WORKSPACE staging/
		cp -r -p ../../cc/ staging/
		rm -rfd staging/cc/tensorflow
		docker build --build-arg PROJECT=${PROJECT} -f mggtp-Dockerfile -t "gcr.io/$(PROJECT)/mg-gtp:$(VERSION_TAG)" .

gtp-push: gtp
	    gcloud docker --verbosity=error -- push "gcr.io/$(PROJECT)/mg-gtp:$(VERSION_TAG)"

clean:
		rm -rfd staging/
.PHONY: gtp gtp-push clean
