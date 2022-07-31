from robyn import Robyn

app = Robyn(__file__)


app.add_directory(route="/",
                  directory_path="./frontend/build",
                  index_file="index.html", show_files_listing=True)
app.start(port=5000)
