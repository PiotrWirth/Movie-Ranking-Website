from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,FloatField,IntegerField
from wtforms.validators import DataRequired
import requests
import os

AUTHORIZATION = os.environ.get("AUTHORIZATION")
SECRET_KEY = os.environ.get("SECRET_KEY")
API_KEY = os.environ.get("API_KEY")

url = "https://api.themoviedb.org/3/search/movie?include_adult=True&language=en-US&page=1"

headers = {
    "accept": "application/json;charset=utf-8'",
    "Authorization": AUTHORIZATION
}



db = SQLAlchemy()

app = Flask(__name__)

app.config['SECRET_KEY'] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"

Bootstrap5(app)

db.init_app(app)

class EditForm(FlaskForm):
    rating = FloatField(label='Your rating out of 10', validators=[DataRequired()])
    review = StringField(label='Your review', validators=[DataRequired()])
    submit = SubmitField(label='Done')

class AddForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Done')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer,nullable=False)
    description = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer,nullable=True)
    review = db.Column(db.String, nullable=True)
    img_url = db.Column(db.String, nullable=False)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()
    for index, movie in enumerate(result):
        movie.ranking = len(result)-index
        db.session.commit()
    movies = db.session.execute(db.select(Movie).order_by(Movie.ranking)).scalars()
    
    
    return render_template("index.html",movies=movies)

@app.route('/edit',methods=['GET','POST'])
def edit():
    movie_id = request.args.get("id")
    edit_form = EditForm()
    movie = db.get_or_404(Movie, movie_id)
    if edit_form.validate_on_submit():
        movie.rating = edit_form.rating.data
        movie.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=edit_form,movie=movie)

@app.route('/delete/<int:index>')
def delete(index):
    movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == index)).scalar()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods=['GET','POST'])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        query = {
        'api_key': API_KEY,
        'query': add_form.title.data,
        }
        response = requests.get(url,params=query, headers=headers)
        data = response.json()['results']
        return render_template('select.html',data=data)
    return render_template('add.html',form=add_form)

@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    url_movie = f"https://api.themoviedb.org/3/movie/{movie_api_id}"
    query_movie = {
    'api_key': API_KEY,
    }
    response = requests.get(url_movie,params=query_movie, headers=headers)
    movie = response.json()
    new_movie = Movie(title=movie['original_title'],year=movie['release_date'],description=movie['overview'],img_url=f"https://image.tmdb.org/t/p/w500/{movie['poster_path']}")
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit',id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
