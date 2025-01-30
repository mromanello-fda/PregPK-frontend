import dash
from dash import html

app = dash.Dash(__name__)

app.layout = html.Div(
    html.A(
        html.Img(
            src="assets/icons/orcid.svg",
            style={"width": "32px", "height": "32px"},  # Adjust size as needed
        ),
        href="https://github.com/someone",
        target="_blank",
    )
)

if __name__ == "__main__":
    app.run_server(debug=True)
