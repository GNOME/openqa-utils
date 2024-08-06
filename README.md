# openQA utilities

A collection of shared helper scripts used for openQA testing in GNOME.

## Usage

The following is an example of how these scripts can be used in a testing pipeline:

```yaml
test:
  image:
    name: registry.opensuse.org/devel/openqa/containers15.5/openqa_worker:latest
    entrypoint: ["/bin/bash", "-c"]
  variables:
    OPENQA_TESTS_GIT: https://gitlab.gnome.org/gnome/openqa-tests
    OPENQA_TESTS_BRANCH: master
    OPENQA_NEEDLES_GIT: https://gitlab.gnome.org/gnome/openqa-needles
    OPENQA_NEEDLES_BRANCH: master
    OPENQA_UTILS_GIT: https://gitlab.gnome.org/gnome/openqa-utils
    OPENQA_UTILS_BRANCH: v1
  before_script:
  # Fetch the tests repo - it contains the actual openQA tests
  - |
    git clone --branch "$OPENQA_TESTS_BRANCH" "$OPENQA_TESTS_GIT" ./openqa
    echo "Checked out $OPENQA_TESTS_GIT commit $(git -C ./openqa rev-parse HEAD)"
  # Fetch openqa-utils repo - it contains helper scripts which we need.
  - |
    git clone --depth 1 --branch "$OPENQA_UTILS_BRANCH" "$OPENQA_UTILS_GIT" ./openqa-utils
    echo "Checked out $OPENQA_UTILS_GIT commit $(git -C ./openqa-utils rev-parse HEAD)"
  - |
    echo "Fetching GNOME OS media"
    url="$(openqa-utils/utils/test_media_url.py  --latest --kind disk --variant sysupdate --arch x86_64)"
    openqa-utils/utils/fetch_test_media.sh $url /data/factory/hdd/disk.img.xz
    unxz /data/factory/hdd/disk.img.xz
  - |
    echo "Expanding GNOME OS media"
    openqa-utils/utils/expand_disk.sh /data/factory/hdd/disk.img 40 GB
  script:
  # Configure openQA worker to run inside the container
  - |
    rm /etc/openqa/*
    cat >/etc/openqa/client.conf <<EOF
    [openqa.gnome.org]
    key = $OPENQA_API_KEY
    secret = $OPENQA_API_SECRET
    EOF
  # Start openQA worker
  - |
    worker_class=qemu_x86_64-${CI_JOB_ID}
    openqa-utils/utils/setup_worker.sh ${worker_class}
    /runopenqa-utils_worker.sh &> worker.log &
  # Submit a job to the controller, which will run in the container.
  - |
    version="master"
    casedir="$(pwd)/openqa"
    echo "casedir is: $casedir"
    openqa-utils/utils/start_all_jobs.sh "${worker_class}" "${version}" "${casedir}" > /tmp/job_ids
  # Wait for completion and report success or failure.
  - openqa-utils/utils/wait_for_job.sh $(cat /tmp/job_ids) > /tmp/exit_code
  - exit $(cat /tmp/exit_code)
  after_script:
  - |
    if [ ! -e /tmp/exit_code ]; then
        echo "Job creation failed, log below."
        cat openqa.log
    fi
  - |
    ./openqa-utils/utils/openqa_junit_report.py $(cat /tmp/job_ids) > ./junit.xml
  artifacts:
    when: always
    paths:
    - junit.xml
    - openqa.log
    - worker.log
    reports:
      junit: junit.xml
```
