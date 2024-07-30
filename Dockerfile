FROM python:3.12

# Due to security reasons, 
# it’s a good practice to run containers as a non-root user.
# Option `--create-home` will create user’s home directory.
# `--shell bin/bash` make sure bash is the default shell.
RUN useradd --create-home --shell /bin/bash dgtmon_user

# Give the user permissions to write to /data directory.
COPY /data /home/dgtmon/data
RUN chown -R dgtmon_user:dgtmon_user /home/dgtmon/data
RUN chmod +rwx------ /home/dgtmon/data

# # Give the user permissions to write to /logs directory.
# # This was commented out, because logs are now written in /tmp/efs.
# COPY /logs /logs
# RUN chown -R dgtmon_user:dgtmon_user /logs
# RUN chmod +rwx------ /logs

# Give pytest permissions to cache tests results.
COPY /tests /home/dgtmon/tests
RUN mkdir /home/dgtmon/tests/.pytest_cache
RUN chown -R dgtmon_user:dgtmon_user /home/dgtmon/tests/.pytest_cache
RUN chmod +rwx------ /home/dgtmon/tests/.pytest_cache
# Give pytest permissions to cache tests auxiliaries.
RUN mkdir /home/dgtmon/.pytest_cache
RUN chown -R dgtmon_user:dgtmon_user /home/dgtmon/.pytest_cache
RUN chmod +rwx------ /home/dgtmon/.pytest_cache

# Add PYTHONPATH to change the search path for libraries.
# The search path should be the same for all of the scripts (inlc. tests).
ENV PYTHONPATH "${PYTHONPATH}:/"

# Change the user to the previously created __dgtmon_user__.
USER dgtmon_user

COPY src/ /home/dgtmon/src
COPY scripts/ /home/dgtmon/scripts
COPY *.whl  /home/dgtmon/

# Copy the requirements.txt file
COPY /requirements.txt /home/dgtmon/requirements.txt

WORKDIR /home/dgtmon

# Install all required packages.
# Disable the cash using `--no-cache-dir` option to lower image size.
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt
# RUN pip install --no-cache-dir -r requirements/prod.txt
# WARNING: The scripts pip, pip3 and pip3.12 are installed in '/home/dgtmon_user/.local/bin' which is not on PATH

# Set bash as default command,
# which will be invoked when docker container runs.
CMD ["bash"]
