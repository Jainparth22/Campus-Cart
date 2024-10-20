import os
from ssp import create_app

os.environ["FLASK_APP"] = "run.py"
app = create_app()



if __name__ == '__main__':
    # Create uploads directory if not exists
    import os
    upload_dir = os.path.join(os.path.dirname(__file__), 'ssp', 'static', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    app.run(host='0.0.0.0',port=8080, debug=True)


