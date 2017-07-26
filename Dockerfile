FROM python:3.5
ADD /backend /
ADD wait_rabbit.sh /wait_rabbit.sh
CMD ['chmod +x /wait_rabbit.sh']
RUN pip install -r reqs.txt