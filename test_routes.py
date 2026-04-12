from app import app

def test_routes():
    with app.test_client() as client:
        client.get('/surveys')
        client.get('/surveys/1')

if __name__ == '__main__':
    test_routes()
