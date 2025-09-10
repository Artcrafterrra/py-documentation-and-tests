from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from cinema.models import Movie, Genre, Actor
from cinema.serializers import (
    MovieListSerializer,
    MovieDetailSerializer,
)


def sample_genre(name="Adventure"):
    return Genre.objects.create(name=name)


def sample_actor(first_name="Alice", last_name="Johnson"):
    return Actor.objects.create(first_name=first_name, last_name=last_name)


def sample_movie(**params):
    defaults = {
        "title": "Sample Movie",
        "description": "Sample description",
        "duration": 110,
    }
    defaults.update(params)
    return Movie.objects.create(**defaults)


MOVIE_URL = reverse("cinema:movie-list")


class MovieViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass"
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpass"
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_movie_detail(self):
        movie = sample_movie()
        movie.genres.add(sample_genre())
        movie.actors.add(sample_actor())

        url = reverse("cinema:movie-detail", args=[movie.id])
        res = self.client.get(url)

        serializer = MovieDetailSerializer(movie)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_list_movies(self):
        movie = sample_movie()
        movie.genres.add(sample_genre())
        movie.actors.add(sample_actor())

        res = self.client.get(MOVIE_URL)

        movies = Movie.objects.all().prefetch_related("genres", "actors")
        serializer = MovieListSerializer(movies, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_movies_by_genres(self):
        genre1 = sample_genre(name="Thriller")
        genre2 = sample_genre(name="Comedy")

        movie1 = sample_movie(title="Seven")
        movie2 = sample_movie(title="The Mask")

        movie1.genres.add(genre1)
        movie2.genres.add(genre2)

        res = self.client.get(MOVIE_URL, {"genres": f"{genre1.id}"})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "Seven")

    def test_filter_movies_by_title(self):
        sample_movie(title="Arrival")
        sample_movie(title="Blade Runner")

        res = self.client.get(MOVIE_URL, {"title": "Arrival"})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "Arrival")

    def test_filter_movies_by_actors(self):
        actor1 = sample_actor(first_name="Robert", last_name="Downey")
        actor2 = sample_actor(first_name="Chris", last_name="Evans")

        movie1 = sample_movie(title="Captain America")
        movie2 = sample_movie(title="Iron Man")

        movie1.actors.add(actor2)
        movie2.actors.add(actor1)

        res = self.client.get(MOVIE_URL, {"actors": f"{actor1.id}"})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "Iron Man")

    def test_create_movie(self):
        genre = sample_genre()
        actor = sample_actor()
        payload = {
            "title": "Brand New Movie",
            "description": "Fresh plot",
            "duration": 130,
            "genres": [genre.id],
            "actors": [actor.id],
        }

        self.client.force_authenticate(user=self.admin)
        res = self.client.post(MOVIE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Movie.objects.filter(title="Brand New Movie").exists())