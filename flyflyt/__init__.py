from flask import Flask
import settings

app = Flask('flyt')
app.config.from_object('flyt.settings')

import views
