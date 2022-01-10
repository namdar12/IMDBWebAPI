import os
import re
from flask.views import MethodView
from wtforms import Form,SubmitField
from flask import Flask,render_template, request
import random
import json
import http.client
import pandas as pd

app = Flask(__name__)


class Homepage(MethodView):

    def get(self):
        return render_template('/index.html')

class randomMovie(MethodView):

    def movie(self):
        self.movie = RandomMovieChooser()
        return self.movie

    def get(self):
        movie = self.movie()
        return render_template('/random_movie.html',movie = movie,image = movie.image_link(),title=movie.movie_title(),
                              year = movie.movie_year())

    def post(self):
        movie = RandomMovieChooser(request.form)
        return render_template('/random_movie.html',movie = movie, image=movie.image_link(),title=movie.movie_title(),
                               year = movie.movie_year())

class popularMovies(MethodView):

    def get(self):
        movie = RandomMovieChooser()
        number_of_movies = movie.number_of_movies()
        return render_template('/most_popular.html', movie = movie.get_movie_df(), number_of_movies = number_of_movies)

class selectedMovie(MethodView):


    def get(self,title):
        movie = RandomMovieChooser()
        movie = movie.movie_choosen(movie_name=title)
        return render_template('/selected_movie.html',movie=movie)


class RandomMovieChooser(Form):
    headers = {'User-agent': 'Chrome/95.0'}
    button = SubmitField("RandomGenerator")

    def image_resize(self, resize_factor, url):
        # Regex for pattern matching relevant parts of the URL
        p = re.compile(".*UX([0-9]*)_CR0,([0-9]*),([0-9]*),([0-9]*).*")
        match = p.search(url)
        if match:
            # Get the image dimensions from the URL
            img_width = str(int(match.group(1)) * resize_factor)
            container_width = str(int(match.group(3)) * resize_factor)
            container_height = str(int(match.group(4)) * resize_factor)

            # Change the image dimensions
            result = re.sub(r"(.*UX)([0-9]*)(.*)", r"\g<1>" + img_width + "\g<3>", url)
            result = re.sub(r"(.*UX[0-9]*_CR0,[0-9]*,)([0-9]*)(.*)", r"\g<1>" + img_width + "\g<3>", result)
            result = re.sub(r"(.*UX[0-9]*_CR0,[0-9]*,[0-9]*,)([0-9]*)(.*)", r"\g<1>" + container_height + "\g<3>",
                            result)
            return result

    def get_movie_df(self):
        if not os.path.exists('test.csv'):
            conn = http.client.HTTPSConnection("imdb-api.com", 443)
            conn.request("GET", "https://imdb-api.com/en/API/MostPopularMovies/k_382ogi2l", headers=self.headers)
            res = conn.getresponse()
            data = res.read()
            movie_dictionary = json.loads(data.decode("utf-8"))
            self.dataframe = pd.DataFrame(movie_dictionary['items'])
            self.dataframe['image'] = self.dataframe['image'].apply(lambda x: self.image_resize(4,x))
            self.dataframe.to_csv('test.csv')
            return self.dataframe
        else:
            self.dataframe = pd.read_csv('test.csv')
            return self.dataframe

    def number_of_movies(self):
        movie_dictionary = self.get_movie_df()
        self.max_movies = len(self.dataframe['id'])
        return self.max_movies

    def movie_picker(self):
        movie_dictionary = self.get_movie_df()
        number = random.randint(0, self.number_of_movies())
        self.movie = movie_dictionary.iloc[number]
        return self.movie

    def image_link(self):
        self.movie_picker()
        return self.movie['image']

    def movie_title(self):
        return self.movie['title']

    def movie_year(self):
        return self.movie['year']

    def movie_choosen(self,movie_name):
        self.movie = self.get_movie_df()[self.get_movie_df()['title'] == movie_name]
        if not self.movie.empty:
            return self.movie
        else:
            return 404





app.add_url_rule('/',view_func=Homepage.as_view('home_page'))
app.add_url_rule('/random',view_func=randomMovie.as_view('random_page'))
app.add_url_rule('/most_popular',view_func=popularMovies.as_view('most_popular'))
app.add_url_rule('/selected_movie/<title>',view_func=selectedMovie.as_view('selected_movie/<title>'),
                 methods=['GET','POST'])


if __name__ == '__main__':
    pd.set_option('display.max_colwidth', None)
    app.run(debug=True)
    try:
        os.remove('test.csv')
    except:
        print("Flask Session Closed")