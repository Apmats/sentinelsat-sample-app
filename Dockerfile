FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

ENV PIPENV_VENV_IN_PROJECT=1

COPY src/app app/app/
COPY Pipfile app/
COPY Pipfile.lock app/

WORKDIR app/

RUN pip install pipenv
RUN pipenv sync --system --verbose

ENV PYTHONPATH="app/"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
