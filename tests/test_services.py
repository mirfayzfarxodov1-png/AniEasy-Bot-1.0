from app.services import parse_episode

def test_parse_plain_number(): assert parse_episode('7') == 7
def test_parse_qism(): assert parse_episode('7-qism') == 7
def test_parse_episode_text(): assert parse_episode('Solo Leveling 12-qism') == 12
def test_parse_missing(): assert parse_episode('salom') is None
