import os
import sys

os.environ["DGTMON_DEBUG"] = "1"
os.environ["FLASK_SECRET_KEY"] = "123"

# Get the parent directory and add it to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


# from src.entrypoint.main import app
# from src.orm.main import app
from src.dashboard.main import app


if __name__ == "__main__":
    app.run(port=8001)
