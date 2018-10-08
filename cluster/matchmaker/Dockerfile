FROM gcr.io/tensor-go/cc-base:0.17

COPY launch_eval.py /app

ADD staging/ /app

CMD ["/bin/sh", "launch_eval.py", "--bucket-name=$MODEL_BUCKET", "--sgf_dir=$SGF_BUCKET"]
