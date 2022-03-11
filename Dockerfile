FROM centos/python-36-centos7:latest
USER root

#define the present working directory
WORKDIR /covid19

ADD . /covid19


RUN yum -y install java-1.8.0-openjdk

RUN pip install --upgrade pip 
RUN pip install -r requirements.txt

ENV FLASK_APP main.py
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_RUN_PORT 8080


####
####
#### OPTIONAL : 4. SET JAVA_HOME environment variable, uncomment the line below if you need it

#ENV JAVA_HOME="/usr/lib/jvm/java-1.8-openjdk"

####

EXPOSE 8080
ADD main.py /
CMD ["flask", "run"]


#### reference link for the Dockerfile

# https://qiita.com/legacyworld/items/1c9ac1d3859a321d6e84

# https://stackoverflow.com/questions/64198813/gae-deploy-error-no-module-named-tabula



