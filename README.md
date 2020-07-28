GNUU K8S Applications
=====================

user
----

User management:

* view/change personal data
* view/change uucp/news config
* view billing data
* view members


jobs
----


Job API for config update

* /update/uucp/config - static uucp config
* /update/uucp/port - statix uucp port
* /update/uucp/passwd  - update uucp user/passwd
* /update/uucp/sys - update uucp sys config
* /update/news/feeds - update newsfeeds
* /update/news/uucp - update uucp batcher

* /update/configmaps - call all functions and write configmaps to K8s
* /reload/newsconf - executes a `ctlinnd reload all konfigs` on the news server


api
---

Webhook API for [Docker Hub](https://github.com/maccyber/micro-dockerhub-hook/)

* /updatenginx - restart nginx deployment



