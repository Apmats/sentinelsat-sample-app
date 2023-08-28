# Simple sentinelsat wrapping service

For this project, we're wrapping sentinelsat inside a FastAPI service, using SQLModel as our ORM, over a Postgres database.


### Design 

In the core of our design, we have one persistent entity. That's the bounding box, and it's associated with 4 floats
and a path to a locally stored image. The definition for this can be found under `models.py`. 
We store one such object after a user has sent us a file for this bounding box coordinates.
We *don't* store any information when we retrieve something from sentinelsat,and that's a conscious choice,
as we want users to be able to retrieve fresh images instead of stale saved data.


Onto the endpoints themselves, we have 3 endpoints as requested. 

First endpoint is `GET images/image` which takes 4 floating numbers to represent a bounding box.
This endpoint either retrieves the saved image for this bounding box, or retrieves an image from sentinetlsat if 
there's no stored image.
This is where sentinelsat usage comes in, and we just query for a specific image (TCI 10m) from the most recent date,
with a low enough cloud coverage, and we return to the user.

Second endpoint is `POST images/image` which also takes 4 floating numbers to represent a bounding box along with
an image file. This endpoint stores the bounding box information, and saves the image file to a directory used
to hold onto these files. We don't store the image binary in the database, to make things easier on us in terms
of database performance, backups etc.

Third endpoint is `GET images/image_color` which also takes 4 floating numbers to represent a bounding box. This
endpoint retrieves either a stored image or an image from sentinelsat. Then it downsizes the image, defines 4 
color classes (represented by a name and an rgb central value) and goes through all the pixels in the image
and assigns those pixels to the closest color class (by comparing to the rgb central value).
In the end, it sums up those values and returns the dominant class out of all of those.


We use pipenv for dependency management, and to be set to run tests you should run:

`pipenv shell`
`pipenv sync --dev`

But apart from that, you should be able to just run the containerized application along with a containerized 
database (check docker-compose.yml) without needing to install anything (apart from docker and compose).

Settings are managed by pydantic (we pass a .env file as the source for environmental variables to our container
and they are read into a setting class).

In terms of tests, we are using some configuration there as well. We override our settings for tests, we create
some temporary directories and we also bring up a Postgres container to test locally with (that happens within 
python code).


### How to test

To do a local manual test of the service, bring up the containers for Postgres and the containerized app:

`docker-compose --build up`

Then you can run curl commands to test the local service

Get an image like this:

`curl -o image.jp2 -X GET "http://localhost:8000/images/image?min_x=23.6&max_x=37.9&min_y=24.2&max_y=38.1"`

Send your own image to be stored like this:

`curl -X POST "http://localhost:8000/images/image?min_x=23.6&max_x=37.9&min_y=24.2&max_y=38.1" -F "file=@image.jp2"`

And finally check what's the picture's dominant color like this:

`curl -X GET "http://localhost:8000/images/image_color?min_x=23.6&max_x=37.9&min_y=24.2&max_y=38.1"`

In addition to manual testing, you can also run all the automated tests, and to do this you can run:

`PYTHONPATH=src python -m pytest test`

### What's missing

We only have 3 endpoints right now, and they're rather simple, so almost all the logic lives under the
`routes/images.py` file. That's okay for now, but as our application grows we should probably split out
the request handling logic (view layer for us) and the domain specific logic (maybe the controller layer).

We only have a few tests per endpoint to showcase how we can write tests for this project, however we should have a 
lot more when trying to make this project production ready - we should aim to cover as many edge cases as we can around
errors that can happen, invalid inputs etc.

We could do better regarding type annotations, and we could add mypy as a precommit hook along with a linter and 
a formatter (black is included but not configured to run automatically).