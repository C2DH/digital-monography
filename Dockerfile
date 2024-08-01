FROM python:3.12

RUN apt-get update && \
    apt-get install -y jq

# Due to security reasons, 
# it’s a good practice to run containers as a non-root user.
# Option `--create-home` will create user’s home directory.
# `--shell bin/bash` make sure bash is the default shell.
RUN useradd --create-home --shell /bin/bash username

# Give the user permissions to write to /data directory.
COPY /data /home/username/dgtmon/data
RUN chown -R username:username /home/username/dgtmon/data
RUN chmod +rwx------ /home/username/dgtmon/data

# # Give the user permissions to write to /logs directory.
# # This was commented out, because logs are now written in /tmp/efs.
# COPY /logs /logs
# RUN chown -R username:username /logs
# RUN chmod +rwx------ /logs

# Give pytest permissions to cache tests results.
COPY /tests /home/username/dgtmon/tests
RUN mkdir /home/username/dgtmon/tests/.pytest_cache
RUN chown -R username:username /home/username/dgtmon/tests/.pytest_cache
RUN chmod +rwx------ /home/username/dgtmon/tests/.pytest_cache
# Give pytest permissions to cache tests auxiliaries.
RUN mkdir /home/username/dgtmon/.pytest_cache
RUN chown -R username:username /home/username/dgtmon/.pytest_cache
RUN chmod +rwx------ /home/username/dgtmon/.pytest_cache

# Give the user permissions to write to /data directory.
RUN chown -R username:username /tmp
RUN chmod +rwx------ /tmp

# Add PYTHONPATH to change the search path for libraries.
# The search path should be the same for all of the scripts (inlc. tests).
ENV PYTHONPATH "${PYTHONPATH}:/"

# Change the user to the previously created __username__.
USER username

COPY src/ /home/username/dgtmon/src
COPY scripts/ /home/username/dgtmon/scripts
COPY *.whl /home/username/dgtmon/
COPY Makefile /home/username/dgtmon/
COPY .versions.json /home/username/dgtmon/.versions.json
COPY requirements.txt /home/username/dgtmon/requirements.txt

WORKDIR /home/username/dgtmon

# Install all required packages.
# Disable the cash using `--no-cache-dir` option to lower image size.
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt
# The scripts pip, pip3 and pip3.12 are installed in '/home/username/dgtmon/.local/bin' which is not on PATH

# Set bash as default command,
# which will be invoked when docker container runs.
CMD ["bash"]
