from flask import Flask
import settings

app = Flask('flyflyt')
app.config.from_object('flyflyt.settings')

import views
