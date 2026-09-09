from app.models import Anime, Episode

def test_anime_model():
    a=Anime(title='Solo Leveling')
    assert a.title == 'Solo Leveling'

def test_episode_model():
    e=Episode(anime_id=1,episode_number=5,telegram_file_id='file')
    assert e.episode_number == 5
