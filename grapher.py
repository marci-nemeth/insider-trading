import plotly.graph_objects as go
from plotly import tools
import plotly.offline as py
import plotly.express as px
import pandas as pd

import numpy as np

df = pd.read_csv("mega_meta_pl.csv", index_col=0)
print(df)
fig = px.scatter(df, x="Market Cap", y="pl5")
fig.show()
