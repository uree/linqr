# Use the Python3.6.9 image
FROM python:3.6.9-stretch

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install the dependencies
RUN pip install -r requirements.txt
# for pandoc
RUN apt-get update && apt-get -y install texlive-latex-recommended

# Run the command to start gunicorn
CMD ["gunicorn", "-e", "SCRIPT_NAME=/linqr" ,"app:app", "-b", "0.0.0.0:9900", "-t 180"]
